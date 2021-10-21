#!/usr/bin/env python
# coding: utf-8

# In[1]:


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
import ctwRTS

################ dynamic dashboards ######################
class dashboard:
   def __init__(self, id, uid, grafana_api, rts,
      start_date, end_date, 
      data_source, refresh_intervals):
      self.id = id
      self.uid = uid
      self.start_date = start_date
      self.end_date = end_date
      self.data_source = data_source
      self.refresh_intervals = refresh_intervals
      self.grafana_api = grafana_api
      self.rts = rts

   def delete(self):
      try: 
         self.grafana_api.dashboard.delete_dashboard(dashboard_uid=self.uid)
      except:
         pass

   def addTSPanel(self, ts_name):
      addTsPanelGrafanaDashboard(self.grafana_api,
         dashboard_id=self.uid,
         ts_name = ts_name, start_time=self.start_date,end_time=self.end_date,
         data_source = self.data_source, refresh_intervals=self.refresh_intervals)

#      annotations = [
#         [int(t/1000),["qty: {}".format(qty)]]
#         ]
   def addAnnotations(self, ts_name, annotations):
      for annotation in annotations:
         addAnnotationsToGrafanaPanel(self.grafana_api, 
            [annotation[0] * 1000],
            self.uid, ts_name, annotation[1])

   def DrawGraph(self, ts_name, data, samplerate=None):
      self.rts.DrawGraph(ts_name, data, samplerate)
      self.addTSPanel(ts_name)

class grafana:
   """A simple example class"""
   data_source = "SimpleJson"
   #data_source = "default"
   refresh_intervals=['1s','5s','10s','1m','5m','10m','15m','30m','1h','12h','1d']

   def __init__(self, user, password, host, port, rts_host, rts_port):
      self.user = user
      self.password = password
      self.auth = (self.user, self.password)
      self.host = host
      self.port = port
      self.grafana_api = GrafanaFace(auth=self.auth, host=self.host, port=self.port)
      self.rts_host = rts_host
      self.rts_port = rts_port
      self.rts = ctwRTS.rts(rts_host,rts_port)

   def createDashboard(self, title, start_date=None, 
      end_date = None, 
      data_source=data_source):
      if start_date is None:
         start_date=self.epochtotime(time.time())
      if end_date is None:
         end_date = self.epochtotime(time.time() - (5*60))

      self.id = createGrafanaDashboard(
         self.grafana_api,
         title=title,
         tags=['dfre'],
         refresh_rate='1s',folderId=None)
      self.uid = self.id["uid"]
      return dashboard(self.id, self.uid,self.grafana_api, self.rts,
         start_date, end_date,
         data_source, self.refresh_intervals)

   def epochtotime(self, epoch):
      return datetime.utcfromtimestamp(epoch).strftime('%Y-%m-%dT%H:%M:%SZ')

def createGrafanaDashboard(
   grafana_api, title:str,
   tags:Optional[list]=None, 
   timezone:Optional[str]=None, 
   folderId:Optional[int]=None, 
   dashboard_id:Optional[str]=None, 
   refresh_rate:Optional[str]=None)->str:

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

def addTsPanelGrafanaDashboard( grafana_api, dashboard_id:str,ts_name:str,start_time:Optional[str]=None,end_time:Optional[str]=None,data_source:Optional[str]=None,refresh_intervals:Optional[list]=None,folderId:Optional[list]=None):
    try:
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
    
def addAnnotationsToGrafanaPanel(grafana_api, strucBreaksUnixTS:list,dashboard_uid:str,ts_name,tags:list):
    res=False
    try:
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


# In[ ]:




