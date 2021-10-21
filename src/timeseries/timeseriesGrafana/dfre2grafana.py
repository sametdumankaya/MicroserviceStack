from typing import Optional,List
from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_face import Folder, Annotations
import pandas as pd
import datetime
import run_cython
import numpy as np
import io
import redisai as rai
import ml2rt
import os
import redis as redis
from redistimeseries.client import Client as tsClient
from grafanaFunctions import addPanelGrafanaDashboard, addAnnotationsToGrafanaPanel
from redisaiFunctions import sendModeltoRedisAI, sendToPrediction
import time
import argparse
import sys
import threading
import grafanaTsAgent 
import copy
import pickle
USE_CASE_ID="tsgrafana"
import TimeSeriesL1AnalyticsEvents
import statsmodels.api as sm
from statsmodels.tsa.arima_model import ARIMA

def get_cli_parser() -> argparse.ArgumentParser:
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ## Help0  cli_parser.add_argument('--title', nargs='?', const='dfre2grafana', type=str)
    cli_parser.add_argument('--title', nargs='?', const='dfre2grafana', default='dfre2grafana',type=str,dest='title',action='store')
    cli_parser.add_argument('--grafana_user', nargs='?', const='admin', default='admin',type=str,dest='grafana_user',action='store')
    cli_parser.add_argument('--grafana_pass', nargs='?', const='admin', default='admin',type=str,dest='grafana_pass',action='store')
    cli_parser.add_argument('--grafana_host', nargs='?', const='localhost', default='localhost',type=str,dest='grafana_host',action='store')
    cli_parser.add_argument('--grafana_port', nargs='?', const=8080,default=8080, type=int,dest='grafana_port',action='store')
    cli_parser.add_argument('--redis_host', nargs='?', const='localhost', default='localhost',type=str,dest='redis_host',action='store')
    cli_parser.add_argument('--redis_port', nargs='?', const=6381, default=6381,type=int,dest='redis_port',action='store')
    cli_parser.add_argument('--redists_host', nargs='?', const='localhost', default='localhost',type=str,dest='redists_host',action='store')
    cli_parser.add_argument('--redists_port', nargs='?', const=6380, default=6380,type=int,dest='redists_port',action='store')
    cli_parser.add_argument('--redisai_host', nargs='?', const='localhost',default='localhost', type=str,dest='redisai_host',action='store')
    cli_parser.add_argument('--redisai_port', nargs='?', const=6379,default=6379, type=int,dest='redisai_port',action='store')
    cli_parser.add_argument('--ts_name', nargs='?', const='ts41',default='ts41', type=str,dest='ts_name',action='store')
    return cli_parser

class grafanaDashboard:
    def __init__(self, grafana_api, did, uid,start_date, end_date,data_source:Optional[str]=None,refresh_intervals:Optional[list]=None,folder_id:Optional[int]=None,redis_con:Optional[object]=None,redisai_con:Optional[object]=None,redists_con:Optional[object]=None):
        
        if(data_source is None):data_source="SimpleJson"
        if(refresh_intervals is None):refresh_intervals=['2s','10s','5m','10m','15m','30m','1h','12h','1d']
        if(folder_id is None): folder_id=0          
        
        self.grafana_api=grafana_api
        self.did = did
        self.uid = uid
        self.start_date = start_date
        self.end_date = end_date
        self.panels=[]
        self.data_source = data_source
        self.refresh_intervals = refresh_intervals
        self.folder_id=folder_id
        self.redisai_con=redisai_con
        self.redists_con=redists_con
        self.redis_con=redis_con
        self.folderId=folder_id
    def addTsPanel(self, ts_name,enable_stream=False):
        try:
            res=addPanelGrafanaDashboard(grafana_api=self.grafana_api,
                                     dashboard_id=self.uid,
                                     ts_name = ts_name, start_time=self.start_date,end_time=self.end_date,
                                     data_source = self.data_source, refresh_intervals=self.refresh_intervals,folderId=self.folder_id)
            self.panels.append(res)
            if(not enable_stream):return res
        except Exception as e:
            print(e)
            print("check your grafana settings")                
        if(enable_stream):
            full_data=self.redists_con.range(ts_name, 0,-1,)
            full_data_name=ts_name
            full_data=[(full_data_name,)+xs for xs in full_data]
            window_size=1000
            stream_rate=6
            dataStreamSimulatorId='streamer_1'
            self.dataStreamSimulator(full_data,full_data_name,window_size,stream_rate,dataStreamSimulatorId,forecast_exists=False)
             
    def addAnnotations(self, ts_name,annotations,tags:Optional[list]=None,text_note:Optional[str]=None):
        try:
            res= addAnnotationsToGrafanaPanel(grafana_api=self.grafana_api,
                                      strucBreaksUnixTS=annotations,dashboard_uid=self.uid,ts_name=ts_name,tags=tags,text_note=text_note)
        except Exception as e:
            print(e)
            print("check your grafana settings")                
      
    def getPanels(self):
        return self.panels
       
    def deleteDashboard(self):
        try:
            res=self.grafana_api.dashboard.delete_dashboard(dashboard_uid=self.uid)
            del self
        except Exception as e:
            print(e)
            print("check your grafana settings")    
    def addTsPanelWithForecast(self,inputTimeSeries:str,outputTimeSeries:str,model_name:Optional[str]=None,model_type:Optional[str]=None,send_to_redists:Optional[bool]=None,test_script_name:Optional[str]=None,window_size:Optional[int]=None,num_predictions:Optional[int]=None,sampling_rate:Optional[int]=None,enable_stream=False):
        if(model_name is None):model_name="my_model"
        if(model_type is None):model_type="onnx"
        model_fname=model_name+"."+model_type
        if(send_to_redists is None):send_to_redists=True
        if(window_size is None):window_size=100
        if(num_predictions is None):num_predictions=1000
        if(sampling_rate is None):sampling_rate=10000
        if(outputTimeSeries is None):outputTimeSeries=test_data_name+"_forecast"
        test_data_name=inputTimeSeries
        last_time_stamp=(self.redists_con.get(test_data_name))[0]
        test_data=self.redists_con.range(test_data_name, 0,-1)
        _, test_data = zip(*test_data)
        test_data=[float(i) for i in test_data]        
        try:
            res=sendModeltoRedisAI(self.redisai_con,model_name,model_type,model_fname)
            res=sendToPrediction(test_data_name,test_data,last_time_stamp,
                             sampling_rate,model_name,model_type,outputTimeSeries,
                             send_to_redists,self.redisai_con,self.redists_con,test_script_name,
                             window_size,num_predictions)
            #add actual data
            _=self.addTsPanel(test_data_name)
            #get the dashboard
            db=self.grafana_api.dashboard.get_dashboard(self.uid)
            #add new time series
            panel_id=0
            panels=db["dashboard"]["panels"]
            for p in panels:
                if(p["targets"][0]["target"]==ts_name):
                    panel_id=p["id"]
                    break
            actual_ts=db["dashboard"]["panels"][panel_id-1]["targets"][0]
            actual_ts["refId"]="A"
            forecast_ts=dict(actual_ts)
            forecast_ts["refId"]="B"
            forecast_ts["target"]=outputTimeSeries
            db["dashboard"]["panels"][panel_id-1]["targets"].append(forecast_ts)
            new_end_time=db["dashboard"]["time"]["to"]
            time_difference = num_predictions * sampling_rate
            if(new_end_time=='now'):
                new_end_time= round(time.time()*1000)
            else:
                new_end_time=datetime.datetime.strptime(new_end_time,'%Y-%m-%dT%H:%M:%SZ')
                new_end_time = time.mktime(new_end_time.timetuple()) * 1000
            new_end_time=datetime.datetime.utcfromtimestamp(new_end_time/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
            db["dashboard"]["time"]["to"]=new_end_time
            db["dashboard"]["folderId"]=self.folderId
            db["meta"]["folderId"]=self.folderId
            res=self.grafana_api.dashboard.update_dashboard(dashboard=db)
            self.uid=res["uid"]
            self.did=res["id"]
            return res
        except Exception as e:
            print(e)
            return None
    def dataStreamSimulator(self,full_data, full_data_name, window_size=1000, stream_rate=2,dataStreamSimulatorId='streamer_1',forecast_exists=False):
        stop_sig=self.redis_con.lpop(dataStreamSimulatorId)
        if(stop_sig is not None): stop_sig=str(d2g.redis.lpop(dataStreamSimulatorId).decode("utf-8"))
        while(stop_sig is None or not(stop_sig =='die')):
            iter_no=1
            end_index=0 
            while(end_index<=len(full_data)):
                start_index=(iter_no-1)*window_size
                end_index=start_index+window_size
                output_data=full_data[start_index:end_index]
                if(len(output_data)==window_size):
                       self.redists_con.delete(full_data_name)
                       self.redists_con.create(ts_name, labels={'full_name':ts_label,'l2category':' ','source':' '})
                       self.redists_con.madd(output_data)
                       ts_sum_info=self.redists_con.info(full_data_name).__dict__
                       first_time_stamp=ts_sum_info["first_time_stamp"]
                       last_time_stamp=ts_sum_info["lastTimeStamp"]
                       start_date=datetime.datetime.utcfromtimestamp(first_time_stamp/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
                       end_date=datetime.datetime.utcfromtimestamp(last_time_stamp/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
                       db=self.grafana_api.dashboard.get_dashboard(self.uid)
                       db["dashboard"]["time"]["from"]=start_date
                       db["dashboard"]["time"]["to"]=end_date
                       res=self.grafana_api.dashboard.update_dashboard(dashboard=db)
                       self.uid=res["uid"]
                       self.did=res["id"]
                       if(end_index!=len(full_data)):time.sleep(stream_rate)
                iter_no+=1
            stop_sig=self.redis_con.lpop(dataStreamSimulatorId)
        
    def addStructuralBreaks(self,ts_name,window_size=1000):
        #redists_con=tsClient(host="localhost", port=6380)
        #values=redists_con.range(ts_name, 0,-1)
        # for i in range(20):
        #     redists_con.add('x',round(time.time()*ms2mc+10000+i),i+5)
        # data=redists_con.range('try',0,-1)
        # round(time.time()*ms2mc
        values=self.redists_con.range(ts_name, 0,-1)
        values=values[-window_size:]
        ts,data = map(list,zip(*values))
        strucBreaks=run_cython.OptimizedPelt(model=run_cython.OptimizedNormalCost()).fit(np.array(data)).predict(3)
       
        d = {'values':data}
        df = pd.DataFrame(data=d)
        strucBreaks=(TimeSeriesL1AnalyticsEvents.removeFPBreaks(df,strucBreaks,model='l1'))[0]
        tmpBreaks=[]
        last_smallest_added=False
        for i in range(0,len(strucBreaks)-1):
            first_br=strucBreaks[i]
            second_br=strucBreaks[i+1]
            if(second_br-first_br>3):
                if(last_smallest_added==False):
                    tmpBreaks.append(first_br)
                last_smallest_added=False
            else:
                if(last_smallest_added==False):
                   tmpBreaks.append(first_br)
                   last_smallest_added=True
        annotations=[]
        for br in tmpBreaks:
            annotations.append(ts[br])
        self.addAnnotations(ts_name,annotations)
    def addSarima(self, ts_name,window_size=1000):
        values=self.redists_con.range(ts_name, 0,-1)
        values=values[-window_size:]
        ts,data = map(list,zip(*values))
        values=np.array(data)
        mod = ARIMA(values, order=(5,1,0))
        res = mod.fit(disp=False)
        pred=res.predict()
        
class Dfre2grafana:
    def __init__(self, grafana_user:str,grafana_pass:str,grafana_host:str,grafana_port:int,
                 redis_host:str, redis_port:int, 
                 redists_host:str,redists_port:int,
                 redisai_host:str, redisai_port:int,
                 grafana_timeout:Optional[float]=None):
      #grafana
        self.grafana_user = grafana_user
        self.grafana_pass = grafana_pass
        self.grafana_auth = (self.grafana_user, self.grafana_pass)
        self.grafana_host = grafana_host
        self.grafana_port = grafana_port
        if(grafana_timeout is None): grafana_timeout=5.0
        self.grafana_timeout=grafana_timeout
        self.grafana_api = GrafanaFace(
                            auth=self.grafana_auth,
                            host=self.grafana_host,
                            port=self.grafana_port,
                            timeout=self.grafana_timeout
                            )
        #redis
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=0)
        #redis time series
        self.redists=tsClient(host=redists_host, port=redists_port)
        #redisai
        self.redisai=rai.Client(host=redisai_host, port=redisai_port)
        #latest folder
        self.folderId=None
    def createFolder(self,title:str):
        #Returns a folder json
        res=self.grafana_api.folder.create_folder(title)
        self.folder_id=res["id"]
        return res
    def createDashboard(self, title:str,start_date, end_date, tags:Optional[list]=None,timezone:Optional[str]=None,
                           folderId:Optional[int]=None,dashboard_id:Optional[str]=None,refresh_rate:Optional[str]=None):
        #Returns a dashboard
        if(tags is None): tags=""
        if(timezone is None): timezone="browser"
        if(folderId is None): folderId=self.folder_id
        if(folderId is None): folderId=0
        if(refresh_rate is None):refresh_rate="5s"
        #TODO:MOVE THIS TO INPUT JSON
        dashboard_dict={
                  "dashboard": {
                    "id": None,
                    "uid": None,
                    "title": title,
                    "tags": tags,
                    "timezone": timezone,
                    "schemaVersion": 16,
                    "version": 0,
                    "annotations":{},
                    "editable":True,
                    "gnetId":None,
                    "graphTooltip":0,
                    "links":None,
                    "style":"dark",
                    "refresh": refresh_rate,
                    
                  },
                  "folderId": folderId,
                  "overwrite": True
                }
        try:
            res=self.grafana_api.dashboard.update_dashboard(dashboard=dashboard_dict)
        except Exception as e:
            print(e)
            print("Check your Grafana authorization key & server's address")
            return
        if(res["status"]=="success"):
            d=grafanaDashboard(grafana_api=self.grafana_api,did=res["id"],uid=res["uid"],start_date=start_date,end_date=end_date,redis_con=self.redis,redisai_con=self.redisai,redists_con=self.redists)
            return d
        else:
            return None
        
#TODO: MAIN LATER
def main(args: List[str]):
    cli_parser = get_cli_parser(args)
    
    cli_options = cli_parser.parse_args(args)
    d2g=Dfre2grafana(cli_options.grafana_user,cli_options.grafana_pass,cli_options.grafana_host,cli_options.grafana_port,\
                          cli_options.redis_host,cli_options.redis_port,
                          cli_options.redists_host,cli_options.redists_port,
                          cli_options.redisai_host,cli_options.redisai_port)
    #number of dashboards
    con_r=redis.Redis(cli_options.redis_host,cli_options.redis_port)
    num_dashboards=con_r.get("num_dashboards")
    if(num_dashboards is None):
        num_dashboards=0
        con_r.set("num_dashboards",num_dashboards)
    folderId=0
    ts_name=cli_options.ts_name
    rts = tsClient(host=cli_options.redists_host, port=cli_options.redists_port)
    ts_sum_info=rts.info(ts_name).__dict__
    first_time_stamp=ts_sum_info["first_time_stamp"]
    last_time_stamp=ts_sum_info["lastTimeStamp"]
    start_date=datetime.datetime.utcfromtimestamp(first_time_stamp/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date=datetime.datetime.utcfromtimestamp(last_time_stamp/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
    tags=['dfre','testing']
    #create a dashboard
    dashboard=d2g.createDashboard(title=cli_options.title,start_date=start_date,end_date=end_date,tags=tags,folderId=folderId)
    num_dashboards=int(num_dashboards)+1
    agent_id="d2g"+str(num_dashboards)
    con_r.set("num_dashboards",num_dashboards) #next agent
    print("An agent created with the id=",agent_id,"listening to redis")
    t1 = threading.Thread(target=grafanaTsAgent.grafanaTsAgentLoop, args=(agent_id,d2g,dashboard,))
    t1.start()
    return agent_id,d2g

if __name__ == "__main__":
    args=sys.argv[1:]
    cli_parser = get_cli_parser()
    cli_options = cli_parser.parse_args(args)
    d2g=Dfre2grafana(cli_options.grafana_user,cli_options.grafana_pass,cli_options.grafana_host,cli_options.grafana_port,\
                          cli_options.redis_host,cli_options.redis_port,
                          cli_options.redists_host,cli_options.redists_port,
                          cli_options.redisai_host,cli_options.redisai_port)
    ts_name=cli_options.ts_name
    folderId=0

    tags=['dfre','testing']
    start_date="now-5m"
    end_date="now"
    
    
    #ADD AN EMPTY DASHBOARD
    db=d2g.createDashboard(title="Event1-Leading Indicators",start_date=start_date,end_date=end_date,tags=tags,folderId=folderId)
    
    #ADD DYNAMICALLY 
    ts_names=['ts939','ts940','ts992', 'ts949']
    for ts_name in ts_names:
        result=db.addTsPanel(ts_name)
    
    #ADD STRUCTURAL BREAK ANALYSIS
    for ts_name in ts_names:
        result=db.addStructuralBreaks(ts_name,window_size=3000)
        time.sleep(1)
    
    #ADD FORECAST
    db=d2g.createDashboard(title="Event1-Leading Indicators",start_date=start_date,end_date=end_date,tags=tags,folderId=folderId)
    for ts_name in ts_names:
        outputTimeSeries=ts_name+"_forecast"
        result2=db.addTsPanelWithForecast(inputTimeSeries=ts_name,outputTimeSeries=outputTimeSeries,model_name="my_model",model_type="onnx")





















    