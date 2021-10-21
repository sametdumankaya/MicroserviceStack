from typing import Optional
def addPanelGrafanaDashboard(grafana_api,dashboard_id,ts_name,start_time,end_time,data_source,refresh_intervals,folderId):
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
        db['dashboard']["folderId"]=folderId
        db['meta']['folderId']=folderId
        try:
            res=grafana_api.dashboard.update_dashboard(dashboard=db)
            
        except Exception as e:
            print(e)
            print("Check your Grafana authorization key & server's address")
            return
        return res

def addAnnotationsToGrafanaPanel(grafana_api,strucBreaksUnixTS:list, dashboard_uid:str, ts_name:str,tags:Optional[dict]=None,text_note:Optional[str]=None):
        try:
            db=grafana_api.dashboard.get_dashboard(dashboard_uid)
        except Exception as e:
            print(e)
            return None
        if(tags is None):tags=['dfre']
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
            if (text_note is None):
                response=grafana_api.annotations.add_annotation(did,panel_id,int(i),int(i),tags,str(cnt)+". structural break")
            else:
                response=self.grafana_api.annotations.add_annotation(did,panel_id,int(i),int(i),tags,text_note)
        print(str(cnt)+"structural breaks added to the graph...")
        return response