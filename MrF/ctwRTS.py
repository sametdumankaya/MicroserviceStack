#!/usr/bin/python3
import argparse
import sys
import time
import os
import random
import math
from typing import Optional
from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_face import Folder, Annotations
import webbrowser
import pandas as pd
import time
from datetime import datetime
from redistimeseries.client import Client

class rts:
   """A simple example class"""

   accountkey = "hg_log:CashBalance"
   positionkey = "hg_log:PositionBalance"
   transactionCount = "hg_log:transactionCount"

   def __init__(self, host='localhost', port=6379):
      self.rts = Client(port=port, host=host)

   def DrawGraph(self, ts_name, data, samplerate=None):
      rts = self.rts
      starttime = time.time()
      now = int(starttime * 1000)
      print("epoch: {}".format(now))
      rts.delete(ts_name)
      datapoints = len(data)
      if samplerate is None:
         timeinterval = 5 * 60 * 1000
      else:
         timeinterval = samplerate * datapoints

      stepsize = int(timeinterval / datapoints)
      starti = now - timeinterval
      timestamps = range(starti, now, stepsize)
      for i in range(datapoints):
         rts.add(ts_name, timestamps[i],data[i])

   def createPosition(self, mode, sym, qty, strategyInstanceKey="test:instance"):
      rts = self.rts
      pricekey = "rts1:01:symbol:{}:price".format(sym)
      sympositionqty =  "position:{}:symbol:{}:qty".format(strategyInstanceKey , sym)
      curprice = rts.get(pricekey)[1]
      print("curprice: {}".format(curprice))
      initialbalance = rts.get(self.accountkey)[1]
      
      if mode == 'buy':
         totalcost = curprice * qty
         print("paid {} for {} shares of {}".format(totalcost, qty, sym))
         rts.decrby(self.accountkey, totalcost)
         rts.incrby(sympositionqty, qty)
   
      elif mode == 'sell':
         totalrevenue = curprice * qty
         print("sold {} shares of {} for {}".format(qty, sym, totalrevenue))
         rts.incrby(self.accountkey, totalrevenue)
         rts.decrby(sympositionqty, qty)
   
      else:
         print("invalid mode: {}".format(mode))
   
      curbalance = rts.get(self.accountkey)[1]
      print("prior balance: {}, current balance: {}".format(initialbalance,curbalance))
   
   i = 12345
   def f(self):
      return 'hello world'

################ dynamic dashboards ######################
def createGrafanaDashboard(auth:str,host:str,port:int,title:str,tags:Optional[list]=None,timezone:Optional[str]=None,
                           folderId:Optional[int]=None,dashboard_id:Optional[str]=None,refresh_rate:Optional[str]=None)->str:
    grafana_api = GrafanaFace(
        auth=auth,
        host=host,
        port=port
        )
    if(tags is None): tags=""
    if(timezone is None): timezone="browser"
    if(folderId is None): folderId=0
    if(refresh_rate is None):refresh_rate="5s"
    #TODO:MOVE THIS TO INPUT JSON
    dashboard={
              "dashboard": {
                "id": None,
                "uid": dashboard_id,
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
        res=grafana_api.dashboard.update_dashboard(dashboard=dashboard)
    except Exception as e:
        print(e)
        print("Check your Grafana authorization key & server's address")
        return
    if(res["status"]=="success"):
        return res
    else:
        return

def addTsPanelGrafanaDashboard(auth:str,host:str,port:int,dashboard_id:str,ts_name:str,start_time:Optional[str]=None,end_time:Optional[str]=None,data_source:Optional[str]=None,refresh_intervals:Optional[list]=None,folderId:Optional[list]=None):
    try:
        grafana_api = GrafanaFace(
        auth=auth,
        host=host,
        port=port
        )
        db=grafana_api.dashboard.get_dashboard(dashboard_id)
    except Exception as e:
        print(e)
        return
    if(start_time is not None and end_time is not None): db['dashboard'].update({"time":{"from":start_time,"to":end_time}})
    if(refresh_intervals is not None): db['dashboard'].update({"timepicker":{"refresh_intervals":refresh_intervals}})
    if(data_source is None):data_source="SimpleJson"
    if(folderId is None):folderId=0 #General folder
    if("panels" not in db['dashboard'].keys()):
        db['dashboard'].update({"panels":[]})
    
    #TODO:THIS IS A BUGGY LOGIC. FAILS IN PARALLEL FOLDER PROCESSING
    panel_id=len(db['dashboard']["panels"])+1
    #TODO:THIS IS A BUGGY LOGIC. FAILS IN PARALLEL FOLDER PROCESSING
    
    #TODO: 4X4. MAKE THIS A CLI INPUT
    col=panel_id%4
    if(col==0): col=4
    row=panel_id//4
    if(panel_id%4==0): row=row-1
    x=(col-1)*6
    y=row*6
    #TODO:MOVE THIS TO INPUT JSON
    panel= {
      "aliasColors": {},
      "bars": False,
      "dashLength": 10,
      "dashes": False,
      "datasource": data_source,
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 6,
        "w": 6,
        "x":x,
        "y": y
      },
      "hiddenSeries": False,
      "id":panel_id,
      "legend": {
        "avg": False,
        "current": False,
        "max": False,
        "min": False,
        "show": True,
        "total": False,
        "values": False
      },
      "lines": True,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "dataLinks": []
      },
      "percentage": False,
      "pointradius": 2,
      "points": False,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": False,
      "steppedLine": False,
      "targets": [
        {
          "refId": None,
          "target": ts_name,
          "type": "timeserie"
        }
      ],
      "thresholds": [],
      "timeFrom": None,
      "timeRegions": [],
      "timeShift": None,
      "title": ts_name,
      "tooltip": {
        "shared": True,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": None,
        "mode": "time",
        "name": None,
        "show": True,
        "values": []
      },
      "yaxes": [
        {
          "format": "short",
          "label": None,
          "logBase": 1,
          "max": None,
          "min": None,
          "show": True
        },
        {
          "format": "short",
          "label": None,
          "logBase": 1,
          "max": None,
          "min": None,
          "show": True
        }
      ],
      "yaxis": {
        "align": False,
        "alignLevel": None
      }
    }

    db['dashboard']["panels"].append(panel)
    db['meta']['folderId']=folderId
    try:
        res=grafana_api.dashboard.update_dashboard(dashboard=db)
        
    except Exception as e:
        print(e)
        print("Check your Grafana authorization key & server's address")
        return
    return res
    
def addAnnotationsToGrafanaPanel(auth:tuple,host:str,port:int,strucBreaksUnixTS:list,dashboard_uid:str,ts_name,tags:list):
    res=False
    try:
        grafana_api = GrafanaFace(
        auth=auth,
        host=host,
        port=port
        )
        db=grafana_api.dashboard.get_dashboard(dashboard_uid)
    except Exception as e:
        print(e)
        return res
    did=db["dashboard"]["id"]
    panel_id=0
    panels=db["dashboard"]["panels"]
    for p in panels:
        if(p["targets"][0]["target"]==ts_name):
            panel_id=p["id"]
            break
    cnt=0
    for i in strucBreaksUnixTS:
        cnt=cnt+1
        grafana_api.annotations.add_annotation(did,panel_id,int(i),int(i),tags,str(cnt)+". structural break")

    print(str(cnt)+"structural breaks added to the graph...")
    res=True
    return res


def HiThere():
   print("hello world!")

