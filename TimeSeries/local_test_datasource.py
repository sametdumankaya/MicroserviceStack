from timeSeriesMain import TimeSeriesOperations
import os

env_params = {
    "redis_host": "localhost",
    "redis_port": 6379,
    "output_redis_host": "localhost",
    "output_redis_port": 6379,
    "from_time": 0,
    "to_time": -1,
    "aggregation_type": "last",
    "bucket_size_msec": 1000,
    "num_regimes": 20,
    "input_filters": "TARGET=TRADING_DATASOURCE",
    "ts_freq_threshold": 50,
    "peek_ratio": 0.3,
    "enablePlotting": True,
    "enablePrediction": True,
    "enablePercentChange": True,
    "window": 10,
    "timeZone": "US/Pacific",
    "output_stream_name": "OUTPUT_DATASOURCE",
    "process_period": 600,
    "enableBatch": False,
    "miniBatchTimeWindow": 2,
    "miniBatchSize": 200,
    "enableStreaming": False,
    "operation_mode": "mp",
    "percent_change_event_ratio": 0.05,
    "percent_change_indicator_ratio": 0.025,
    "custom_changepoint_function_name": "",
    "custom_changepoint_function_script": "",
    "chow_penalty": 10,
    "model": "l1",
    "enableFillMissingDataWithLast": False,
    "file_url": "",
    "enableOnlineMonitor": False,
    "ts_list": "rts1:01:symbol:AAPL:volume,"
               "rts1:01:symbol:AAPL:price,"
               "rts1:01:symbol:MSFT:volume,"
               "rts1:01:symbol:MSFT:price,"
               "rts1:01:symbol:GOOG:volume,"
               "rts1:01:symbol:GOOG:price",
    "subsequenceLength": 10,
    "windowSize": 10,
    "excl_factor": 1,
    "n_regimes": 2,
    "stream_refresh_rate": 10,
    "percent_change_threshold": 0.05,
    "percent_window": 2,
    "last_minutes_count": 5,
    "refresh_interval": "10s",
    "dashboard_title": "My Streaming Datasource Dashboard"
}

for p in env_params:
    os.environ[p] = str(env_params[p])

time_series_operations = TimeSeriesOperations(os.getenv('redis_host', "localhost"),
                                              int(os.getenv('redis_port', 6379)),
                                              os.getenv('output_redis_host', "localhost"),
                                              int(os.getenv('output_redis_port', 6379)))

time_series_operations.process_time_series(
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
