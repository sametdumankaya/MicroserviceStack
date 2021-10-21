import datetime
import json
import os
import uuid
from typing import List, Optional

import pymysql.cursors
import redis.exceptions
import uvicorn
from fastapi import FastAPI, HTTPException
from grafana_api.grafana_face import GrafanaFace
from pydantic import BaseModel
from redis import Redis
from redistimeseries.client import Client


class Annotation(BaseModel):
    time_stamp: int
    description: str
    tag: Optional[str] = ""


class AddAnnotationsRequest(BaseModel):
    dashboard_id: int
    panel_id: int
    annotations: List[Annotation]


class SetDashboardTimeRangeRequest(BaseModel):
    dashboard_id: int
    time_range_start: str
    time_range_end: str


class TimeSeriesVis(BaseModel):
    time_series_name: str


class CreateTimeSeriesGraphsRequest(BaseModel):
    time_series_info_list: List[TimeSeriesVis]
    title: str
    time_range_start: str
    time_range_end: str
    datasource: Optional[str] = None


class CreateStreamingTimeSeriesGraphsRequest(BaseModel):
    streaming_time_series_info_list: List[TimeSeriesVis]
    title: str
    last_minutes_count: int
    refresh_interval: str
    datasource: Optional[str] = None


class CreateOutputTablesRequest(BaseModel):
    output_name: str
    dashboard_name: str


class UpdateOutputTableDashboardRequest(BaseModel):
    dashboard_id: int
    dashboard_name: str
    output_name: str


class CreateVideoDashboardRequest(BaseModel):
    video_url: str
    dashboard_title: str


class ThresholdStep(BaseModel):
    color: str
    value: Optional[float] = None


class Threshold(BaseModel):
    name: str
    threshold_steps: List[ThresholdStep]


class CreateDiagramDashboardRequest(BaseModel):
    mermaid_markup: str
    dashboard_name: str
    live_data_key: str
    streaming_interval_ms: int
    log_key_name: str
    thresholds: List[Threshold]


class CreatePNLDashboardRequest(BaseModel):
    start: float
    end: float
    title: str


counter = 0
while True:
    try:
        if counter % 10000 == 0:
            print(
                f"Trying to connect mysql at host: {os.getenv('mysql_host', 'localhost')}, "
                f"database: {os.getenv('mysql_database', 'magi')}, "
                f"port: {os.getenv('mysql_port', '3307')}")
        mysql_connection = pymysql.connect(host=os.getenv('mysql_host', "localhost"),
                                           port=int(os.getenv("mysql_port", "3307")),
                                           user=os.getenv('mysql_user', "magi"),
                                           password=os.getenv('mysql_password', "magi"),
                                           database=os.getenv('mysql_database', "magi"),
                                           cursorclass=pymysql.cursors.DictCursor)
        print("Connected!")
        break
    except:
        if counter % 10000 == 0:
            print("Connection failed. Trying again")
        counter += 1
        continue

counter = 0
while True:
    try:
        if counter % 10000 == 0:
            print(
                f"Trying to connect grafana at host: {os.getenv('grafana_host', 'localhost')}, user: {os.getenv('grafana_user', 'admin')}")
        grafana_api = GrafanaFace(
            auth=(os.getenv('grafana_user', 'admin'), os.getenv('grafana_password', 'admin')),
            host=os.getenv('grafana_host', 'localhost'),
            port=int(os.getenv('grafana_port', '3000')))
        print("Connected!")
        break
    except:
        if counter % 10000 == 0:
            print("Connection failed. Trying again")
        counter += 1
        continue

# noinspection PyUnboundLocalVariable
cursor = mysql_connection.cursor()
redis_client = Redis(host="localhost", port=6379, decode_responses=True)
rts = Client(redis_client)
app = FastAPI(title="Vis API")


def get_output_table_dashboard_dict(output_name: str, histogram_base64: str, events_base64: str, dashboard_title: str,
                                    metadata: dict, dashboard_id: int = None, dashboard_uid: str = None,
                                    version: int = 0, latest_dashboard_version: int = None):
    metadata_str = "# Metadata\n\n"
    for key, value in metadata.items():
        metadata_str += f"* #### {key} = {str(value)}\n"
    dashboard = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "gnetId": None,
        "graphTooltip": 0,
        "id": dashboard_id,
        "links": [],
        "panels": [
            {
                "datasource": "MySQL",
                "fieldConfig": {
                    "defaults": {
                        "color": {
                            "mode": "thresholds"
                        },
                        "custom": {
                            "align": None,
                            "filterable": False
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
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
                    "h": 9,
                    "w": 24,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "showHeader": True
                },
                "pluginVersion": "7.4.3",
                "targets": [
                    {
                        "format": "table",
                        "group": [],
                        "metricColumn": "none",
                        "rawQuery": True,
                        "rawSql": f"SELECT contribution, indicator, event FROM magi.contributors WHERE output_name = '{output_name}' AND version = {version};",
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
                "timeFrom": None,
                "timeShift": None,
                "title": "Contributors",
                "type": "table"
            },
            {
                "datasource": "MySQL",
                "fieldConfig": {
                    "defaults": {
                        "color": {
                            "mode": "thresholds"
                        },
                        "custom": {
                            "align": None,
                            "filterable": False
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
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
                    "h": 8,
                    "w": 24,
                    "x": 0,
                    "y": 9
                },
                "id": 2,
                "options": {
                    "showHeader": True
                },
                "pluginVersion": "7.4.3",
                "targets": [
                    {
                        "format": "table",
                        "group": [],
                        "metricColumn": "none",
                        "rawQuery": True,
                        "rawSql": f"SELECT leading_indicator, main_indicator, trailing_indicator FROM magi.events WHERE output_name = '{output_name}' AND version = {version};",
                        "refId": "A",
                        "select": [
                            [
                                {
                                    "params": [
                                        "id"
                                    ],
                                    "type": "column"
                                }
                            ]
                        ],
                        "table": "events",
                        "timeColumn": "id",
                        "timeColumnType": "int",
                        "where": [
                            {
                                "name": "$__unixEpochFilter",
                                "params": [],
                                "type": "macro"
                            }
                        ]
                    }
                ],
                "title": "Events",
                "type": "table"
            },
            {
                "datasource": "MySQL",
                "fieldConfig": {
                    "defaults": {
                        "color": {
                            "mode": "thresholds"
                        },
                        "custom": {
                            "align": None,
                            "filterable": False
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
                                },
                                {
                                    "color": "red",
                                    "value": 80
                                }
                            ]
                        }
                    },
                    "overrides": [
                        {
                            "matcher": {
                                "id": "byName",
                                "options": "leading_indicator"
                            },
                            "properties": [
                                {
                                    "id": "custom.width",
                                    "value": 445
                                }
                            ]
                        }
                    ]
                },
                "gridPos": {
                    "h": 8,
                    "w": 24,
                    "x": 0,
                    "y": 17
                },
                "id": 3,
                "options": {
                    "showHeader": True,
                    "sortBy": []
                },
                "pluginVersion": "7.4.3",
                "targets": [
                    {
                        "format": "table",
                        "group": [],
                        "metricColumn": "none",
                        "rawQuery": True,
                        "rawSql": f"SELECT leading_indicator, main_indicator, trailing_indicator FROM magi.indicators WHERE output_name = '{output_name}' AND version = {version};",
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
                "title": "Indicators",
                "type": "table"
            },
            {
                "datasource": None,
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 13,
                    "w": 8,
                    "x": 0,
                    "y": 25
                },
                "id": 4,
                "options": {
                    "content": f"<div>\n  <img src=\"{histogram_base64}\" alt=\"Histogram of Regime Changes\" />\n</div>",
                    "mode": "markdown"
                },
                "pluginVersion": "7.4.3",
                "timeFrom": None,
                "timeShift": None,
                "title": "Histogram of Regime Changes",
                "type": "text"
            },
            {
                "datasource": None,
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 13,
                    "w": 7,
                    "x": 8,
                    "y": 25
                },
                "id": 5,
                "options": {
                    "content": f"<div>\n  <img src=\"{events_base64}\" alt=\"Histogram of Events\" />\n</div>",
                    "mode": "markdown"
                },
                "pluginVersion": "7.4.3",
                "timeFrom": None,
                "timeShift": None,
                "title": "Histogram of Events",
                "type": "text"
            },
            {
                "datasource": None,
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 13,
                    "w": 9,
                    "x": 15,
                    "y": 25
                },
                "id": 6,
                "options": {
                    "content": metadata_str,
                    "mode": "markdown"
                },
                "pluginVersion": "7.4.3",
                "timeFrom": None,
                "timeShift": None,
                "title": "Metadata",
                "type": "text"
            }
        ],
        "schemaVersion": 27,
        "style": "dark",
        "tags": [],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-6h",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "",
        "title": dashboard_title,
        "uid": str(uuid.uuid4()),
        "version": latest_dashboard_version
    }

    return dashboard


def get_pnl_dashboard(start: float, end: float, title: str):
    return {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "gnetId": None,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "panels": [
            {
                "datasource": None,
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 9,
                    "w": 8,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "content": f"<div align=\"center\">\n  <p style=\"font-size:60px;\">Starting Cash</p>\n</div>\n<div align=\"center\">\n  <p style=\"font-size:90px;\">${round(start, 2):,}</p>\n</div>",
                    "mode": "markdown"
                },
                "pluginVersion": "7.3.10",
                "timeFrom": None,
                "timeShift": None,
                "title": "",
                "type": "text"
            },
            {
                "datasource": None,
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 9,
                    "w": 8,
                    "x": 8,
                    "y": 0
                },
                "id": 2,
                "options": {
                    "content": f"<div align=\"center\">\n  <p style=\"font-size:60px;\">Ending Cash</p>\n</div>\n<div align=\"center\">\n  <p style=\"font-size:90px;\">${round(end, 2):,}</p>\n</div>",
                    "mode": "markdown"
                },
                "pluginVersion": "7.3.10",
                "timeFrom": None,
                "timeShift": None,
                "title": "",
                "type": "text"
            },
            {
                "datasource": None,
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 9,
                    "w": 8,
                    "x": 16,
                    "y": 0
                },
                "id": 3,
                "options": {
                    "content": f"<div align=\"center\">\n  <p style=\"font-size:60px;\">Profit and Loss</p>\n</div>\n<div align=\"center\">\n  <p style=\"font-size:90px;\">${round(end - start, 2):,}</p>\n</div>",
                    "mode": "markdown"
                },
                "pluginVersion": "7.3.10",
                "timeFrom": None,
                "timeShift": None,
                "title": "",
                "type": "text"
            }
        ],
        "refresh": False,
        "schemaVersion": 26,
        "style": "dark",
        "tags": [],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-5m",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "",
        "title": title,
        "uid": None,
        "version": 1
    }


def get_dashboard_panels_for_timeseries(time_series_info_list, datasource: str = None):
    panels = []
    for index, key in enumerate(time_series_info_list):
        panels.append({
            "aliasColors": {},
            "bars": False,
            "dashLength": 10,
            "dashes": False,
            "datasource": datasource,
            "fieldConfig": {
                "defaults": {
                    "custom": {}
                },
                "overrides": []
            },
            "fill": 1,
            "fillGradient": 0,
            "gridPos": {
                "h": 9,
                "w": 12,
                "x": 0 if index % 2 == 0 else 12,
                "y": index * 9
            },
            "hiddenSeries": False,
            "id": index + 1,
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
                "alertThreshold": True
            },
            "percentage": False,
            "pluginVersion": "7.4.3",
            "pointradius": 2,
            "points": False,
            "renderer": "flot",
            "seriesOverrides": [],
            "spaceLength": 10,
            "stack": False,
            "steppedLine": False,
            "targets": [
                {
                    "aggregation": "",
                    "command": "ts.range",
                    "keyName": key.time_series_name.strip(),
                    "query": "",
                    "refId": "A",
                    "type": "timeSeries"
                }
            ],
            "thresholds": [],
            "timeFrom": None,
            "timeRegions": [],
            "timeShift": None,
            "title": key.time_series_name.strip(),
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
        })
    return panels


def get_timeseries_dashboard_dict(time_series_info_list, start_date_time, end_date_time, title, is_streaming=False,
                                  refresh_interval=None, datasource: str = None):
    panels = get_dashboard_panels_for_timeseries(time_series_info_list, datasource)
    dashboard = {
        "annotations": {
            "list": [
                {
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "#5794F2",
                    "limit": 100,
                    "name": "BLUE",
                    "showIn": 0,
                    "tags": [
                        "BLUE"
                    ],
                    "type": "tags"
                },
                {
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "#FADE2A",
                    "limit": 100,
                    "name": "SELL",
                    "showIn": 0,
                    "tags": [
                        "YELLOW"
                    ],
                    "type": "tags"
                },
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                },
                {
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "#5794F2",
                    "limit": 100,
                    "matchAny": True,
                    "name": "Custom annotations",
                    "showIn": 0,
                    "tags": [],
                    "type": "tags"
                }
            ]
        },
        "editable": True,
        "gnetId": None,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "panels": panels,
        "refresh": refresh_interval if is_streaming and refresh_interval is not None else False,
        "schemaVersion": 27,
        "style": "dark",
        "tags": [],
        "templating": {
            "list": []
        },
        "time": {
            "from": start_date_time,
            "to": end_date_time
        },
        "timepicker": {
            "refresh_intervals": [
                refresh_interval
            ]
        } if is_streaming and refresh_interval else {},
        "timezone": "",
        "title": title,
        "uid": None,
        "version": 0
    }

    return dashboard


def add_annotations_to_dashboard(dashboard_id, panel_id, annotations):
    if annotations and len(annotations) > 0:
        for annotation in annotations:
            grafana_api.annotations.add_annotation(dashboard_id,
                                                   panel_id,
                                                   annotation.time_stamp,
                                                   0,
                                                   [annotation.tag] if annotation.tag else [],
                                                   annotation.description)


def update_dashboard_time_range(dashboard_id, start_date_time, end_date_time):
    dashboard_uid = grafana_api.search.search_dashboards(dashboard_ids=dashboard_id)[0]['uid']
    dashboard = grafana_api.dashboard.get_dashboard(dashboard_uid)
    dashboard["dashboard"]["time"]["from"] = start_date_time
    dashboard["dashboard"]["time"]["to"] = end_date_time
    grafana_api.dashboard.update_dashboard(dashboard={'dashboard': dashboard["dashboard"]})


def create_or_update_output_tables(output_name: str, dashboard_name: str, dashboard_id: int = None):
    data = redis_client.xrevrange(output_name, count=1)
    data_dict = json.loads(data[0][1]["data"])
    version = data_dict["metadata"]["loop_no"]
    events = data_dict["events"]
    indicators = data_dict["indicators"]
    contributors = data_dict["contributors"]
    plots = data_dict["plots"]
    metadata = data_dict["metadata"]

    events_to_insert = []
    if len(events) > 0:
        for i in range(len(events["leading indicator"])):
            events_to_insert.append((
                events["leading indicator"][str(i)],
                events["main indicator"][str(i)],
                events["trailing indicator"][str(i)],
                output_name,
                version
            ))
        sql = "INSERT INTO `events` (`leading_indicator`, `main_indicator`, `trailing_indicator`, `output_name`, `version`) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(sql, events_to_insert)

    indicators_to_insert = []
    if len(indicators) > 0:
        for i in range(len(indicators["leading indicator"])):
            indicators_to_insert.append((
                ",".join(indicators["leading indicator"][str(i)]),
                ",".join(indicators["main indicator"][str(i)]),
                ",".join(indicators["trailing indicator"][str(i)]),
                output_name,
                version
            ))
        sql = "INSERT INTO `indicators` (`leading_indicator`, `main_indicator`, `trailing_indicator`, `output_name`, `version`) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(sql, indicators_to_insert)

    contributors_to_insert = []
    if len(contributors) > 0:
        for i in range(len(contributors["contribution"])):
            contributors_to_insert.append((
                contributors["contribution"][str(i)],
                contributors["indicator"][str(i)],
                contributors["event"][str(i)],
                output_name,
                version
            ))
        sql = "INSERT INTO `contributors` (`contribution`, `indicator`, `event`, `output_name`, `version`) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(sql, contributors_to_insert)

    # if no histogram or events plot available, use placeholder image to show there is no data available
    plot_histogram = "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHN2ZyBQVUJMSUMgIi0vL1czQy8vRFREIFNWRyAxLjEvL0VOIiAiaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTEuZHRkIj4KPCEtLSBDcmVhdG9yOiBDb3JlbERSQVcgWDcgLS0+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWw6c3BhY2U9InByZXNlcnZlIiB3aWR0aD0iMTA1bW0iIGhlaWdodD0iODRtbSIgdmVyc2lvbj0iMS4xIiBzdHlsZT0ic2hhcGUtcmVuZGVyaW5nOmdlb21ldHJpY1ByZWNpc2lvbjsgdGV4dC1yZW5kZXJpbmc6Z2VvbWV0cmljUHJlY2lzaW9uOyBpbWFnZS1yZW5kZXJpbmc6b3B0aW1pemVRdWFsaXR5OyBmaWxsLXJ1bGU6ZXZlbm9kZDsgY2xpcC1ydWxlOmV2ZW5vZGQiCnZpZXdCb3g9IjAgMCAxMDUwMCA4NDAwIgogeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiPgogPGRlZnM+CiAgPHN0eWxlIHR5cGU9InRleHQvY3NzIj4KICAgPCFbQ0RBVEFbCiAgICAuZmlsMCB7ZmlsbDojQkFDNENFfQogICAgLmZpbDEge2ZpbGw6I0UwNjUwMDtmaWxsLXJ1bGU6bm9uemVyb30KICAgXV0+CiAgPC9zdHlsZT4KIDwvZGVmcz4KIDxnIGlkPSLQodC70L7QuV94MDAyMF8xIj4KICA8bWV0YWRhdGEgaWQ9IkNvcmVsQ29ycElEXzBDb3JlbC1MYXllciIvPgogIDxnIGlkPSJfOTczOTU1OTIwIj4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHRyYW5zZm9ybT0ibWF0cml4KDIuMTI5OTVFLTAxNCAtOC4zNTA0MSAwLjgwNDIyMyAyLjIxMTU3RS0wMTMgMTUwNi4yNCA2NzE0LjkpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogICA8cGF0aCBjbGFzcz0iZmlsMSIgZD0iTTM2NTUgNDM5NWwwIC0xMDI4IC0yMDIgMCAwIDY0NiAtNDQwIC02NDYgLTIwNyAwIDAgMTAyOCAyMDIgMCAwIC02NzEgNDUyIDY3MSAxOTUgMHptNjg3IDE4YzI4NywwIDQ5NiwtMjIyIDQ5NiwtNTMyIDAsLTMwOSAtMjA5LC01MzEgLTQ5NiwtNTMxIC0yODYsMCAtNDk1LDIyMiAtNDk1LDUzMSAwLDMxMCAyMDksNTMyIDQ5NSw1MzJ6bTAgLTE5NGMtMTc1LDAgLTI4NywtMTQ2IC0yODcsLTMzOCAwLC0xOTIgMTEyLC0zMzcgMjg3LC0zMzcgMTc1LDAgMjg4LDE0NSAyODgsMzM3IDAsMTkyIC0xMTMsMzM4IC0yODgsMzM4em0xNDI2IDE3NmMyOTcsMCA1MDQsLTIwNCA1MDQsLTUxNCAwLC0zMDkgLTIwNywtNTE0IC01MDQsLTUxNGwtMzc0IDAgMCAxMDI4IDM3NCAwem0wIC0xOTNsLTE3MiAwIDAgLTY0MyAxNzIgMGMxOTUsMCAyOTcsMTQxIDI5NywzMjIgMCwxNzUgLTEwOSwzMjEgLTI5NywzMjF6bTE1MzMgMTkzbC0zNjUgLTEwMjggLTI1MyAwIC0zNjcgMTAyOCAyMzAgMCA2MCAtMTc0IDQwNyAwIDU4IDE3NCAyMzAgMHptLTM0NCAtMzY3bC0yOTUgMCAxNDggLTQ0MyAxNDcgNDQzem04MTQgMzY3bDAgLTgzNiAyNzYgMCAwIC0xOTIgLTc1NiAwIDAgMTkyIDI3NyAwIDAgODM2IDIwMyAwem0xMjQ5IDBsLTM2NiAtMTAyOCAtMjUzIDAgLTM2NiAxMDI4IDIzMCAwIDYwIC0xNzQgNDA2IDAgNTkgMTc0IDIzMCAwem0tMzQ0IC0zNjdsLTI5NiAwIDE0OCAtNDQzIDE0OCA0NDN6Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB4PSIxNjQ1IiB5PSI2NTc3IiB3aWR0aD0iNzc0MyIgaGVpZ2h0PSIxMzgiLz4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHg9IjExMTMiIHk9IjY1NzciIHdpZHRoPSI1MzIiIGhlaWdodD0iMTM4Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB0cmFuc2Zvcm09Im1hdHJpeCgyLjEyOTk1RS0wMTQgLTAuODA0MjI0IDAuODA0MjIzIDIuMTI5OTVFLTAxNCA5MjQ5LjA3IDcxMDguNTYpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogICA8cmVjdCBjbGFzcz0iZmlsMCIgeD0iMTExMyIgeT0iNDc4MiIgd2lkdGg9IjUzMiIgaGVpZ2h0PSIxMzgiLz4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHg9IjExMTMiIHk9IjI5ODYiIHdpZHRoPSI1MzIiIGhlaWdodD0iMTM4Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB0cmFuc2Zvcm09Im1hdHJpeCgyLjEyOTk1RS0wMTQgLTAuODA0MjI0IDAuODA0MjIzIDIuMTI5OTVFLTAxNCA2NjY4LjEzIDcxMDguNTYpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogICA8cmVjdCBjbGFzcz0iZmlsMCIgdHJhbnNmb3JtPSJtYXRyaXgoMi4xMjk5NUUtMDE0IC0wLjgwNDIyNCAwLjgwNDIyMyAyLjEyOTk1RS0wMTQgNDA4Ny4xOCA3MTA4LjU2KSIgd2lkdGg9IjY2MSIgaGVpZ2h0PSIxNzIiLz4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHg9IjExMTUiIHk9IjExOTEiIHdpZHRoPSI1MzIiIGhlaWdodD0iMTM4Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB0cmFuc2Zvcm09Im1hdHJpeCgyLjEyOTk1RS0wMTQgLTAuODA0MjI0IDAuODA0MjIzIDIuMTI5OTVFLTAxNCAxNTA2LjI0IDcxMDguNTYpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogIDwvZz4KIDwvZz4KPC9zdmc+Cg=="
    plot_events = "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHN2ZyBQVUJMSUMgIi0vL1czQy8vRFREIFNWRyAxLjEvL0VOIiAiaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTEuZHRkIj4KPCEtLSBDcmVhdG9yOiBDb3JlbERSQVcgWDcgLS0+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWw6c3BhY2U9InByZXNlcnZlIiB3aWR0aD0iMTA1bW0iIGhlaWdodD0iODRtbSIgdmVyc2lvbj0iMS4xIiBzdHlsZT0ic2hhcGUtcmVuZGVyaW5nOmdlb21ldHJpY1ByZWNpc2lvbjsgdGV4dC1yZW5kZXJpbmc6Z2VvbWV0cmljUHJlY2lzaW9uOyBpbWFnZS1yZW5kZXJpbmc6b3B0aW1pemVRdWFsaXR5OyBmaWxsLXJ1bGU6ZXZlbm9kZDsgY2xpcC1ydWxlOmV2ZW5vZGQiCnZpZXdCb3g9IjAgMCAxMDUwMCA4NDAwIgogeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiPgogPGRlZnM+CiAgPHN0eWxlIHR5cGU9InRleHQvY3NzIj4KICAgPCFbQ0RBVEFbCiAgICAuZmlsMCB7ZmlsbDojQkFDNENFfQogICAgLmZpbDEge2ZpbGw6I0UwNjUwMDtmaWxsLXJ1bGU6bm9uemVyb30KICAgXV0+CiAgPC9zdHlsZT4KIDwvZGVmcz4KIDxnIGlkPSLQodC70L7QuV94MDAyMF8xIj4KICA8bWV0YWRhdGEgaWQ9IkNvcmVsQ29ycElEXzBDb3JlbC1MYXllciIvPgogIDxnIGlkPSJfOTczOTU1OTIwIj4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHRyYW5zZm9ybT0ibWF0cml4KDIuMTI5OTVFLTAxNCAtOC4zNTA0MSAwLjgwNDIyMyAyLjIxMTU3RS0wMTMgMTUwNi4yNCA2NzE0LjkpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogICA8cGF0aCBjbGFzcz0iZmlsMSIgZD0iTTM2NTUgNDM5NWwwIC0xMDI4IC0yMDIgMCAwIDY0NiAtNDQwIC02NDYgLTIwNyAwIDAgMTAyOCAyMDIgMCAwIC02NzEgNDUyIDY3MSAxOTUgMHptNjg3IDE4YzI4NywwIDQ5NiwtMjIyIDQ5NiwtNTMyIDAsLTMwOSAtMjA5LC01MzEgLTQ5NiwtNTMxIC0yODYsMCAtNDk1LDIyMiAtNDk1LDUzMSAwLDMxMCAyMDksNTMyIDQ5NSw1MzJ6bTAgLTE5NGMtMTc1LDAgLTI4NywtMTQ2IC0yODcsLTMzOCAwLC0xOTIgMTEyLC0zMzcgMjg3LC0zMzcgMTc1LDAgMjg4LDE0NSAyODgsMzM3IDAsMTkyIC0xMTMsMzM4IC0yODgsMzM4em0xNDI2IDE3NmMyOTcsMCA1MDQsLTIwNCA1MDQsLTUxNCAwLC0zMDkgLTIwNywtNTE0IC01MDQsLTUxNGwtMzc0IDAgMCAxMDI4IDM3NCAwem0wIC0xOTNsLTE3MiAwIDAgLTY0MyAxNzIgMGMxOTUsMCAyOTcsMTQxIDI5NywzMjIgMCwxNzUgLTEwOSwzMjEgLTI5NywzMjF6bTE1MzMgMTkzbC0zNjUgLTEwMjggLTI1MyAwIC0zNjcgMTAyOCAyMzAgMCA2MCAtMTc0IDQwNyAwIDU4IDE3NCAyMzAgMHptLTM0NCAtMzY3bC0yOTUgMCAxNDggLTQ0MyAxNDcgNDQzem04MTQgMzY3bDAgLTgzNiAyNzYgMCAwIC0xOTIgLTc1NiAwIDAgMTkyIDI3NyAwIDAgODM2IDIwMyAwem0xMjQ5IDBsLTM2NiAtMTAyOCAtMjUzIDAgLTM2NiAxMDI4IDIzMCAwIDYwIC0xNzQgNDA2IDAgNTkgMTc0IDIzMCAwem0tMzQ0IC0zNjdsLTI5NiAwIDE0OCAtNDQzIDE0OCA0NDN6Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB4PSIxNjQ1IiB5PSI2NTc3IiB3aWR0aD0iNzc0MyIgaGVpZ2h0PSIxMzgiLz4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHg9IjExMTMiIHk9IjY1NzciIHdpZHRoPSI1MzIiIGhlaWdodD0iMTM4Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB0cmFuc2Zvcm09Im1hdHJpeCgyLjEyOTk1RS0wMTQgLTAuODA0MjI0IDAuODA0MjIzIDIuMTI5OTVFLTAxNCA5MjQ5LjA3IDcxMDguNTYpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogICA8cmVjdCBjbGFzcz0iZmlsMCIgeD0iMTExMyIgeT0iNDc4MiIgd2lkdGg9IjUzMiIgaGVpZ2h0PSIxMzgiLz4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHg9IjExMTMiIHk9IjI5ODYiIHdpZHRoPSI1MzIiIGhlaWdodD0iMTM4Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB0cmFuc2Zvcm09Im1hdHJpeCgyLjEyOTk1RS0wMTQgLTAuODA0MjI0IDAuODA0MjIzIDIuMTI5OTVFLTAxNCA2NjY4LjEzIDcxMDguNTYpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogICA8cmVjdCBjbGFzcz0iZmlsMCIgdHJhbnNmb3JtPSJtYXRyaXgoMi4xMjk5NUUtMDE0IC0wLjgwNDIyNCAwLjgwNDIyMyAyLjEyOTk1RS0wMTQgNDA4Ny4xOCA3MTA4LjU2KSIgd2lkdGg9IjY2MSIgaGVpZ2h0PSIxNzIiLz4KICAgPHJlY3QgY2xhc3M9ImZpbDAiIHg9IjExMTUiIHk9IjExOTEiIHdpZHRoPSI1MzIiIGhlaWdodD0iMTM4Ii8+CiAgIDxyZWN0IGNsYXNzPSJmaWwwIiB0cmFuc2Zvcm09Im1hdHJpeCgyLjEyOTk1RS0wMTQgLTAuODA0MjI0IDAuODA0MjIzIDIuMTI5OTVFLTAxNCAxNTA2LjI0IDcxMDguNTYpIiB3aWR0aD0iNjYxIiBoZWlnaHQ9IjE3MiIvPgogIDwvZz4KIDwvZz4KPC9zdmc+Cg=="
    if len(plots) > 0:
        plot_histogram = plots["histogram"]
        plot_events = plots["events"]
        plots_to_insert = [(plot_histogram, plot_events, output_name, version)]
        sql = "INSERT INTO `plots` (`histogram`, `events`, `output_name`, `version`) VALUES (%s, %s, %s, %s)"
        cursor.executemany(sql, plots_to_insert)

    metadata_tmp = metadata["parameters"]
    metadata_tmp["start_ts"] = metadata["start_ts"]
    metadata_tmp["end_ts"] = metadata["end_ts"]
    metadata_to_insert = [(json.dumps(metadata_tmp), output_name, version)]
    sql = "INSERT INTO `metadata` (`params_json`, `output_name`, `version`) VALUES (%s, %s, %s)"
    cursor.executemany(sql, metadata_to_insert)
    mysql_connection.commit()

    if dashboard_id is None:
        # Create new dashboard
        dashboard = get_output_table_dashboard_dict(output_name,
                                                    plot_histogram,
                                                    plot_events,
                                                    dashboard_name,
                                                    metadata_tmp,
                                                    version=version)
    else:
        dashboard_uid = grafana_api.search.search_dashboards(dashboard_ids=[dashboard_id])[0]['uid']
        existing_dashboard_id = grafana_api.dashboard.get_dashboard(dashboard_uid)['dashboard']['version']
        dashboard = get_output_table_dashboard_dict(output_name, plot_histogram, plot_events,
                                                    dashboard_name, metadata_tmp, dashboard_id, dashboard_uid, version,
                                                    existing_dashboard_id)

    # Update the existing dashboard
    created_output_table_dashboard = grafana_api.dashboard.update_dashboard(
        dashboard={'dashboard': dashboard})
    return created_output_table_dashboard


def get_streaming_dashboard_dict(stream_url: str, dashboard_title: str):
    return {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "gnetId": None,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "panels": [
            {
                "datasource": None,
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 9,
                    "w": 12,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "autoPlay": True,
                    "loop": True,
                    "videoURL": stream_url,
                    "videoType": "url"  # will be parametric later
                },
                "pluginVersion": "7.4.3",
                "timeFrom": None,
                "timeShift": None,
                "title": "Stream",
                "type": "innius-video-panel"
            }
        ],
        "schemaVersion": 27,
        "style": "dark",
        "tags": [],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-6h",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "",
        "title": dashboard_title,
        "uid": None,
        "version": 0
    }


def get_diagram_dashboard_dict(mermaid_markup: str, dashboard_name: str, live_data_key: str, streaming_interval_ms: int,
                               log_key_name: str, thresholds):
    dashboard_dict = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "gnetId": None,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "panels": [
            {
                "datasource": "Redis",
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "valueName": "last"
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
                                },
                                {
                                    "color": "yellow",
                                    "value": 30
                                },
                                {
                                    "color": "red",
                                    "value": 60
                                }
                            ]
                        }
                    },
                    "overrides": [{
                        "matcher": {
                            "id": "byName",
                            "options": threshold.name
                        },
                        "properties": [
                            {
                                "id": "thresholds",
                                "value": {
                                    "mode": "absolute",
                                    "steps": [
                                        {
                                            "color": step.color,
                                            "value": step.value
                                        } for step in threshold.threshold_steps
                                    ]
                                }
                            }
                        ]
                    } for threshold in thresholds]
                },
                "gridPos": {
                    "h": 13,
                    "w": 24,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "authPassword": "",
                    "authUsername": "",
                    "composites": [],
                    "content": mermaid_markup,
                    "legend": {
                        "asTable": True,
                        "displayMode": "table",
                        "gradient": {
                            "enabled": True,
                            "show": True
                        },
                        "hideEmpty": False,
                        "hideZero": False,
                        "placement": "under",
                        "show": False,
                        "sortBy": "last",
                        "sortDesc": True,
                        "stats": [
                            "mean",
                            "last",
                            "min",
                            "max",
                            "sum"
                        ]
                    },
                    "maxWidth": True,
                    "mermaidServiceUrl": "",
                    "mermaidThemeVariablesDark": {
                        "classDiagram": {},
                        "common": {
                            "fontFamily": "Roboto,Helvetica Neue,Arial,sans-serif"
                        },
                        "flowChart": {},
                        "sequenceDiagram": {},
                        "stateDiagram": {},
                        "userJourneyDiagram": {}
                    },
                    "mermaidThemeVariablesLight": {
                        "classDiagram": {},
                        "common": {
                            "fontFamily": "Roboto,Helvetica Neue,Arial,sans-serif"
                        },
                        "flowChart": {},
                        "sequenceDiagram": {},
                        "stateDiagram": {},
                        "userJourneyDiagram": {}
                    },
                    "metricCharacterReplacements": [],
                    "moddedSeriesVal": 0,
                    "mode": "content",
                    "nodeSize": {
                        "minHeight": 40,
                        "minWidth": 30
                    },
                    "pluginVersion": "7.3.10",
                    "style": "",
                    "useBackground": False,
                    "useBasicAuth": False,
                    "valueName": "last"
                },
                "pluginVersion": "1.7.2",
                "targets": [
                    {
                        "command": "hgetall",
                        "count": 1,
                        "field": "",
                        "keyName": live_data_key,
                        "query": "",
                        "refId": "A",
                        "streaming": True,
                        "streamingInterval": streaming_interval_ms,
                        "type": "command"
                    }
                ],
                "timeFrom": None,
                "timeShift": None,
                "title": "Topology",
                "type": "jdbranham-diagram-panel"
            },
            {
                "datasource": "Redis",
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "align": None,
                            "filterable": False
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
                                },
                                {
                                    "color": "red",
                                    "value": 80
                                }
                            ]
                        }
                    },
                    "overrides": [
                        {
                            "matcher": {
                                "id": "byName",
                                "options": "time"
                            },
                            "properties": [
                                {
                                    "id": "custom.width",
                                    "value": 291
                                }
                            ]
                        }
                    ]
                },
                "gridPos": {
                    "h": 11,
                    "w": 24,
                    "x": 0,
                    "y": 13
                },
                "id": 2,
                "options": {
                    "showHeader": True,
                    "sortBy": [
                        {
                            "desc": True,
                            "displayName": "time"
                        }
                    ]
                },
                "pluginVersion": "7.3.10",
                "targets": [
                    {
                        "command": "hget",
                        "field": log_key_name,
                        "keyName": live_data_key,
                        "query": "",
                        "refId": "A",
                        "streaming": True,
                        "streamingDataType": "TimeSeries",
                        "streamingInterval": streaming_interval_ms,
                        "type": "command"
                    }
                ],
                "timeFrom": None,
                "timeShift": None,
                "title": "Event Log",
                "type": "table"
            }
        ],
        "refresh": False,
        "schemaVersion": 26,
        "style": "dark",
        "tags": [],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-5m",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "",
        "title": dashboard_name,
        "uid": str(uuid.uuid4()),
        "version": 1
    }

    return dashboard_dict


@app.post("/create_timeseries_graphs/")
def create_timeseries_graphs(request: CreateTimeSeriesGraphsRequest):
    rts_temp = Client(Redis(host="localhost", port=6379 if request.datasource is None else 6381, decode_responses=True))
    try:
        info = rts_temp.info(request.time_series_info_list[0].time_series_name)
    except redis.exceptions.ResponseError as e:
        raise HTTPException(status_code=500, detail="One of the time series keys is not available on Redis.")
    first_timestamp = info.first_time_stamp
    last_timestamp = info.lastTimeStamp
    start_datetime = datetime.datetime.fromtimestamp(first_timestamp / 1e3).strftime("%Y-%m-%dT%H:%M:%S")
    end_datetime = datetime.datetime.fromtimestamp(last_timestamp / 1e3).strftime("%Y-%m-%dT%H:%M:%S")
    new_dashboard = get_timeseries_dashboard_dict(request.time_series_info_list, start_datetime, end_datetime,
                                                  request.title, False, datasource=request.datasource)
    created_dashboard = grafana_api.dashboard.update_dashboard(dashboard={'dashboard': new_dashboard})
    return {
        "created_dashboard_id": created_dashboard["id"],
        "dashboard_name": created_dashboard["slug"],
        "panel_ids": list(range(1, len(request.time_series_info_list) + 1))
    }


@app.post("/create_streaming_timeseries_graphs/")
def create_streaming_timeseries_graphs(request: CreateStreamingTimeSeriesGraphsRequest):
    start_datetime = f"now-{request.last_minutes_count}m"
    end_datetime = "now"
    new_streaming_dashboard = get_timeseries_dashboard_dict(request.streaming_time_series_info_list, start_datetime,
                                                            end_datetime, request.title, True, request.refresh_interval,
                                                            datasource=request.datasource)
    created_streaming_dashboard = grafana_api.dashboard.update_dashboard(
        dashboard={'dashboard': new_streaming_dashboard})
    return {
        "created_streaming_dashboard_id": created_streaming_dashboard["id"],
        "dashboard_name": created_streaming_dashboard["slug"],
        "panel_ids": list(range(1, len(request.streaming_time_series_info_list) + 1))
    }


@app.post("/add_annotations/")
def add_annotations(request: AddAnnotationsRequest):
    add_annotations_to_dashboard(request.dashboard_id, request.panel_id, request.annotations)
    return True


@app.post("/set_dashboard_time_range/")
def set_dashboard_time_range(request: SetDashboardTimeRangeRequest):
    update_dashboard_time_range(request.dashboard_id, request.time_range_start, request.time_range_end)
    return True


@app.post("/create_output_tables/")
def create_output_tables(request: CreateOutputTablesRequest):
    created_output_table_dashboard = create_or_update_output_tables(request.output_name, request.dashboard_name)
    return {
        "created_output_table_dashboard": created_output_table_dashboard["id"],
        "dashboard_name": created_output_table_dashboard["slug"]
    }


@app.post("/update_output_tables/")
def update_output_tables(request: UpdateOutputTableDashboardRequest):
    updated_output_table_dashboard = create_or_update_output_tables(request.output_name, request.dashboard_name,
                                                                    request.dashboard_id)
    return {
        "updated_output_table_dashboard": updated_output_table_dashboard["id"],
        "dashboard_name": updated_output_table_dashboard["slug"]
    }


@app.post("/create_video_dashboard/")
def create_video_dashboard(request: CreateVideoDashboardRequest):
    dashboard = get_streaming_dashboard_dict(request.video_url, request.dashboard_title)
    created_video_dashboard = grafana_api.dashboard.update_dashboard(dashboard={'dashboard': dashboard})
    return {
        "created_video_dashboard": created_video_dashboard["id"],
        "dashboard_name": created_video_dashboard["slug"]
    }


@app.post("/create_diagram_dashboard_request/")
def create_diagram_dashboard_request(request: CreateDiagramDashboardRequest):
    dashboard = get_diagram_dashboard_dict(request.mermaid_markup, request.dashboard_name, request.live_data_key,
                                           request.streaming_interval_ms, request.log_key_name, request.thresholds)
    created_diagram_dashboard = grafana_api.dashboard.update_dashboard(dashboard={'dashboard': dashboard})
    return {
        "created_video_dashboard": created_diagram_dashboard["id"],
        "dashboard_name": created_diagram_dashboard["slug"]
    }


@app.post("/create_pnl_dashboard/")
def create_pnl_dashboard(request: CreatePNLDashboardRequest):
    dashboard = get_pnl_dashboard(request.start, request.end, request.title)
    created_pnl_dashboard = grafana_api.dashboard.update_dashboard(dashboard={'dashboard': dashboard})
    return {
        "created_pnl_dashboard": created_pnl_dashboard["id"],
        "dashboard_name": created_pnl_dashboard["slug"]
    }


if __name__ == "__main__":
    workers = int(os.getenv('api_workers', 1))
    api_port = int(os.getenv('api_port', 8001))
    print(f"VisAPI is available on http://localhost:{api_port}")
    uvicorn.run(app, host="0.0.0.0", port=api_port, workers=workers, log_level="warning")
