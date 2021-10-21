from typing import Optional
from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_face import Folder, Annotations
import pandas as pd
import datetime
import time
import numpy as np
import io
import redisai as rai
import ml2rt
import os
import time
from typing import Optional

USE_CASE_ID="timeseries"


def createDashboardEvents(grafana_api, title:str, sql_query:str):
        #Returns a dashboard
        if(tags is None): tags=""
        if(timezone is None): timezone="browser"
        if(folderId is None): folderId=folder_id
        if(folderId is None): folderId=0
        if(refresh_rate is None):refresh_rate="5s"
        #TODO:MOVE THIS TO INPUT JSON
        dashboard_dict={
                      "annotations": {
                        "list": [
                          {
                            "builtIn": 1,
                            "datasource": "-- Grafana --",
                            "enable": true,
                            "hide": true,
                            "iconColor": "rgba(0, 211, 255, 1)",
                            "name": "Annotations & Alerts",
                            "type": "dashboard"
                          }
                        ]
                      },
                      "editable": true,
                      "gnetId": null,
                      "graphTooltip": 0,
                      "id": 237,
                      "links": [],
                      "panels": [
                        {
                          "datasource": "MySQL",
                          "description": "",
                          "fieldConfig": {
                            "defaults": {
                              "custom": {
                                "align": null
                              },
                              "mappings": [],
                              "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                  {
                                    "color": "green",
                                    "value": null
                                  },
                                  {
                                    "color": "red",
                                    "value": 80
                                  }
                                ]
                              }
                            },
                            "overrides": []
                          },
                          "gridPos": {
                            "h": 15,
                            "w": 15,
                            "x": 0,
                            "y": 0
                          },
                          "id": 2,
                          "options": {
                            "showHeader": True
                          },
                          "pluginVersion": "7.0.3",
                          "targets": [
                            {
                              "format": "table",
                              "group": [],
                              "metricColumn": "none",
                              "rawQuery": True,
                              "rawSql": sql_query,
                              "refId": "A",
                              "select": [
                                [
                                  {
                                    "params": [
                                      "value"
                                    ],
                                    "type": "column"
                                  }
                                ]
                              ],
                              "timeColumn": "time",
                              "where": [
                                {
                                  "name": "$__timeFilter",
                                  "params": [],
                                  "type": "macro"
                                }
                              ]
                            }
                          ],
                          "timeFrom": '',
                          "timeShift": '',
                          "title": title,
                          "type": "table"
                        }
                      ],
                      "schemaVersion": 25,
                      "style": "dark",
                      "tags": [],
                      "templating": {
                        "list": []
                      },
                      "time": {
                        "from": "now-6h",
                        "to": "now"
                      },
                      "timepicker": {
                        "refresh_intervals": [
                          "5s",
                          "10s",
                          "1m",
                          "5m",
                          "15m",
                          "30m",
                          "1h",
                          "2h",
                          "1d"
                        ]
                      },
                      "timezone": "browser",
                      "title": "DFRE-Events",
                      "uid": None,
                      "version": 2
                      }
        try:
            res=grafana_api.dashboard.update_dashboard(dashboard=dashboard_dict)
            return res
        except Exception as e:
            print(e)
            print("Check your Grafana authorization key & server's address")
            return None