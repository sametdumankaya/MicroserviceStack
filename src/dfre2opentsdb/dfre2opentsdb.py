import requests
import yaml
import time
from datetime import datetime, timedelta
from otsdb_client import Connection
from datetime import datetime
import warnings
warnings.simplefilter("ignore", category=all)
import pandas as pd
import matrix_profile as MP
import numpy as np
class Dfre2Opentsdb:
    def __init__(self, url="http://spa-cxdp-opentsdb-1.cisco.com:4242"):
        self.url=url
    def getMetrics(self,max_metric=10000):
        query_url=self.url+"/api/suggest?type=metrics&q=&max="+str(max_metric)
        response=requests.get(query_url)
        result= (yaml.safe_load(response.text))
        return result
    def getData(self,metric:str,start:str, end=datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),aggregator="first", counter=True, dropResets=True, 
                downsample="1s-last",fullResponse=False):
        query_url="start="+str(start)+"&end="+str(end)+"&m="+aggregator+":True:"+metric
        query_url=self.url+"/api/query?"+query_url
        result=[]
        response=requests.get(query_url)
        if(fullResponse): 
            resp=yaml.safe_load(response.text)
            if(resp is not None and len(resp)>0): 
                return resp[0]
            else:
                return []
        if(len(response.text)>2):
            result= (yaml.safe_load(response.text))[0]['dps']
            result=list(result.items())
        return result
    def getMultipleData(self,metrics:list,start:str, end=datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),aggregator="avg",rate=True):
        query_url="start=1d-ago"
        for i in range(len(metrics)):
            m=metrics[i]
            query_url=query_url+"&m="+aggregator+":"+m
        query_url=self.url+"/api/query?"+query_url
        print(query_url)
        response=requests.get(query_url)
        return response

def queryAllMetrics(d2o, metrics, start,fullResponse=True):
    all_results=[]
    for m in metrics:
        try:
            result1=d2o.getData(metric=m,start=start,fullResponse=True)
            if(len(result1)>0):
                all_results.append(result1)
        except Exception as e:
            print(e)
            print(m)
    return all_results

def stripDataFromTs(all_results):
    data_stripped=[]
    for d in all_results:
        res = [] 
        for key in d['dps'].keys() : 
            res.append(d['dps'][key])
        data_stripped.append(res)
    return data_stripped

if __name__ == "__main__":
    #define the object
    d2o=Dfre2Opentsdb()
    #get metrics
    metrics=d2o.getMetrics(max_metric=1000000) 
    #get data of the first metric for last 24 hours
    last_hour_date_time = datetime.now() - timedelta(hours = 24)
    start=last_hour_date_time.strftime('%Y/%m/%d-%H:%M:%S')
    start_time = time.time()
    all_results=queryAllMetrics(d2o,metrics,start,fullResponse=True)
    print("It took %s seconds --- to query all metrics" % (time.time() - start_time))
    #get multiple metrics at once
    metrics=['Cisco-IOS-XR-drivers-media-eth-oper_ethernet-interface/statistics/statistic_aborted_packet_drops','Cisco-IOS-XR-drivers-media-eth-oper_ethernet-interface/statistics/statistic_buffer_underrun_packet_drops']
    #this returns a list of dictionaries for each metric. It needs to be stripped
    start='1d-ago'
    response=d2o.getMultipleData(metrics, start)    
    #STRIP DATA FOR LAST HOUR
    data_stripped=stripDataFromTs(all_results)
    #Create a dataframe of all ts for matr
    df = pd.DataFrame(data_stripped)
    df=df.transpose()   
    abp=df.iloc[:,0]
    time_series=abp[abp.notnull()].values.astype(np.float32)
    MP.plotSemanticSegForSingleTS(time_series,n_regimes=2)
    #THIS IS VERY SLOW BECAUSE IT IS FOR ALL TIME SERIES.
    all_cac,all_regimes=getSemanticSegmentationFromMP(df)
