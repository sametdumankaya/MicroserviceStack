from timeSeriesMain import TimeSeriesOperations
import os
import pandas as pd

if __name__ == "__main__":
    time_series_operations = TimeSeriesOperations(os.getenv('redis_host', "localhost"),
                                                  int(os.getenv('redis_port', 6379)),
                                                  os.getenv('output_redis_host', "localhost"),
                                                  int(os.getenv('output_redis_port', 6379)))

    # If file_url variable specified, first download and insert it into redis
    enableOnlineMonitor = os.getenv('enableOnlineMonitor', "False").lower() == "true"
    if enableOnlineMonitor:
        time_series_operations.monitorOnlineTimeSeries(ts_list=os.getenv('ts_list', ""),
                                                       from_time=int(os.getenv('from_time', 0)),
                                                       to_time=int(os.getenv('to_time', -1)),
                                                       operation_mode=os.getenv('operation_mode', "mp"),
                                                       aggregation_type=os.getenv('aggregation_type', "last"),
                                                       bucket_size_msec=int(os.getenv('bucket_size_msec', 1000)),
                                                       chow_penalty=int(os.getenv('chow_penalty', 10)),
                                                       percent_change_threshold=float(
                                                           os.getenv('percent_change_threshold', 0.05)),
                                                       percent_window=int(os.getenv('percent_window', 2)),
                                                       stream_refresh_rate=int(os.getenv('stream_refresh_rate', 10)),
                                                       subsequenceLength=int(os.getenv('subsequenceLength', 10)),
                                                       windowSize=int(os.getenv('windowSize', 10)),
                                                       excl_factor=int(os.getenv('excl_factor', 1)),
                                                       n_regimes=int(os.getenv('n_regimes', 2)),
                                                       last_minutes_count=int(os.getenv('last_minutes_count', 5)),
                                                       refresh_interval=os.getenv('refresh_interval', "1s"),
                                                       dashboard_title=os.getenv('dashboard_title',
                                                                                 "My Streaming Dashboard"))
    else:
        file_url = os.getenv('file_url', "")
        if file_url != "":
            print("Downloading the time series file...")
            df = pd.read_csv(file_url)
            print("Processing the file")
            input_filters = os.getenv("input_filters", "SENSORDOG")
            time_series_operations.analyze_time_series_csv(df,
                                                           from_time=int(os.getenv('from_time', 0)),
                                                           to_time=int(os.getenv('to_time', -1)),
                                                           aggregation_type=os.getenv('aggregation_type', "last"),
                                                           bucket_size_msec=int(os.getenv('bucket_size_msec', 60000)),
                                                           num_regimes=int(os.getenv('num_regimes', 20)),
                                                           filters=os.getenv('input_filters', "SENSORDOG"),
                                                           ts_freq_threshold=int(os.getenv('ts_freq_threshold', 50)),
                                                           peek_ratio=float(os.getenv('peek_ratio', 0.3)),
                                                           enablePlotting=os.getenv('enablePlotting',
                                                                                    "True").lower() == "true",
                                                           enablePrediction=os.getenv('enablePrediction',
                                                                                      "True").lower() == "true",
                                                           enablePercentChange=os.getenv('enablePercentChange',
                                                                                         "True").lower() == "true",
                                                           window=int(os.getenv('window', 10)),
                                                           timeZone=os.getenv('timeZone', "US/Pacific"),
                                                           output_name=os.getenv('output_stream_name',
                                                                                 "SensorDog4TimeSeries"),
                                                           process_period=int(os.getenv('process_period', 600)),
                                                           enableBatch=os.getenv('enableBatch',
                                                                                 "False").lower() == "true",
                                                           miniBatchTimeWindow=int(os.getenv('miniBatchTimeWindow', 2)),
                                                           miniBatchSize=int(os.getenv('miniBatchSize', 200)),
                                                           enableStreaming=os.getenv('enableStreaming',
                                                                                     "False").lower() == "true",
                                                           operation_mode=os.getenv('operation_mode', "mp"),
                                                           # chow #pct #custom
                                                           percent_change_event_ratio=float(
                                                               os.getenv('percent_change_event_ratio', 0.05)),
                                                           percent_change_indicator_ratio=float(
                                                               os.getenv('percent_change_indicator_ratio', 0.025)),
                                                           custom_changepoint_function_name=os.getenv(
                                                               'custom_changepoint_function_name', ""),
                                                           custom_changepoint_function_script=os.getenv(
                                                               'custom_changepoint_function_script', ""),
                                                           chow_penalty=int(os.getenv('chow_penalty', 10)),
                                                           model=os.getenv('model', "l1"),
                                                           enableFillMissingDataWithLast=os.getenv(
                                                               'enableFillMissingDataWithLast',
                                                               "False").lower() == "true")
        else:
            time_series_operations.process_time_series(from_time=int(os.getenv('from_time', 0)),
                                                       to_time=int(os.getenv('to_time', -1)),
                                                       aggregation_type=os.getenv('aggregation_type', "last"),
                                                       bucket_size_msec=int(os.getenv('bucket_size_msec', 60000)),
                                                       num_regimes=int(os.getenv('num_regimes', 20)),
                                                       filters=os.getenv('input_filters', "SENSORDOG"),
                                                       ts_freq_threshold=int(os.getenv('ts_freq_threshold', 50)),
                                                       peek_ratio=float(os.getenv('peek_ratio', 0.3)),
                                                       enablePlotting=os.getenv('enablePlotting',
                                                                                "True").lower() == "true",
                                                       enablePrediction=os.getenv('enablePrediction',
                                                                                  "True").lower() == "true",
                                                       enablePercentChange=os.getenv('enablePercentChange',
                                                                                     "True").lower() == "true",
                                                       window=int(os.getenv('window', 10)),
                                                       timeZone=os.getenv('timeZone', "US/Pacific"),
                                                       output_name=os.getenv('output_stream_name',
                                                                             "SensorDog4TimeSeries"),
                                                       process_period=int(os.getenv('process_period', 600)),
                                                       enableBatch=os.getenv('enableBatch', "False").lower() == "true",
                                                       miniBatchTimeWindow=int(os.getenv('miniBatchTimeWindow', 2)),
                                                       miniBatchSize=int(os.getenv('miniBatchSize', 200)),
                                                       enableStreaming=os.getenv('enableStreaming',
                                                                                 "False").lower() == "true",
                                                       operation_mode=os.getenv('operation_mode', "mp"),
                                                       # chow #pct #custom
                                                       percent_change_event_ratio=float(
                                                           os.getenv('percent_change_event_ratio', 0.05)),
                                                       percent_change_indicator_ratio=float(
                                                           os.getenv('percent_change_indicator_ratio', 0.025)),
                                                       custom_changepoint_function_name=os.getenv(
                                                           'custom_changepoint_function_name', ""),
                                                       custom_changepoint_function_script=os.getenv(
                                                           'custom_changepoint_function_script', ""),
                                                       chow_penalty=int(os.getenv('chow_penalty', 10)),
                                                       model=os.getenv('model', "l1"),
                                                       enableFillMissingDataWithLast=os.getenv(
                                                           'enableFillMissingDataWithLast', "False").lower() == "true")
