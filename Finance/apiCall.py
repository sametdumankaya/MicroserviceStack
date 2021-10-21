
import requests
import json
import time
class ApiCall:
    def Call(paramName):
        url = 'http://localhost:8000/start_time_series_analysis/'
        params = {
          "redis_host": "localhost",
          "redis_port": 6381,
          "output_redis_host": "localhost",
          "output_redis_port": 6379,
          "from_time": 0,
          "to_time": -1,
          "aggregation_type": "last",
          "bucket_size_msec": 60000,
          "num_regimes": 20,
          "input_filters": "SYMSET=ACTIVE_"+paramName,
          "ts_freq_threshold": 20,
          "peek_ratio": 0.3,
          "enablePlotting": True,
          "enablePrediction": True,
          "enablePercentChange": True,
          "window": 10,
          "timeZone": "US/Pacific",
          "output_stream_name": "MAGI_"+paramName,
          "process_period": 600,
          "enableBatch": True,
          "miniBatchTimeWindow": 2,
          "miniBatchSize": 5,
          "enableStreaming": False,
          "operation_mode": "pct",
          "percent_change_event_ratio": 0.05,
          "percent_change_indicator_ratio": 0.025,
          "custom_changepoint_function_name": "",
          "custom_changepoint_function_script": "",
          "chow_penalty": 10,
          "model": "l1",
          "enableFillMissingDataWithLast": False,
          "file_url": "",
          "enableOnlineMonitor": False,
          "ts_list": "test1,test2",
          "subsequenceLength": 10,
          "windowSize": 10,
          "excl_factor": 1,
          "n_regimes": 2,
          "stream_refresh_rate": 10,
          "percent_change_threshold": 0.05,
          "percent_window": 2,
          "last_minutes_count": 5,
          "refresh_interval": "1s",
          "dashboard_title": "My Streaming Dashboard"
        }
        # Adding empty header as parameters are being sent in payload
        headers = { "Accept":"application/json","Content-Type": "application/json" }
        r = requests.post(url, data=json.dumps(params), headers=headers)
        print("Status Code:",r.status_code)
        jsonObject = json.loads(r.text)
        print("\nContainer name: ",jsonObject["container_name"])
        print("\nImage name: ",jsonObject["image_name"])
        print("\nContainer id: ",jsonObject["container_id"])
        print("\nStart at: ",jsonObject["startedAt"])
        print("\nStatus: ",jsonObject["status"])
        print("\nLogs: ",jsonObject["logs"])
        return {
            "container_id":jsonObject["container_id"]
        }




