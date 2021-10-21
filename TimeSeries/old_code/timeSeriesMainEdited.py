# -*- coding: utf-8 -*-
"""
SensorDog TimeSeries Analysis Main Functionality
"""

import timeSeriesFunctions
import os
import pprint
import time
import redis
import distutils
env_variables = {
    "redis_host": os.getenv('redis_host', "localhost"),
    "redis_port": int(os.getenv('redis_port', 6379)),
    "output_redis_host": os.getenv('output_redis_host', "localhost"),
    "output_redis_port": int(os.getenv('output_redis_port', 6379)),
    "from_time": int(os.getenv('from_time', 0)),
    "to_time": int(os.getenv('to_time', -1)),
    "aggregation_type": os.getenv('aggregation_type', "last"),
    "bucket_size_msec": int(os.getenv('bucket_size_msec', 60000)),
    "num_regimes": int(os.getenv('num_regimes', 20)),
    "filters": os.getenv('filters', "TARGET=SENSORDOG"),
    "ts_freq_threshold": int(os.getenv('ts_freq_threshold', 50)),
    "peek_ratio": float(os.getenv('peek_ratio', 0.3)),
    "enablePlotting": os.getenv('enablePlotting', "True").lower() == "true",
    "enablePrediction": os.getenv('enablePrediction', "True").lower() == "true",
    "enablePercentChange": os.getenv('enablePercentChange', "True").lower() == "true",
    "window": int(os.getenv('window', 10)),
    "timeZone": os.getenv('timeZone', "US/Pacific"),
    "output_name": os.getenv('output_name', "SensorDog4TimeSeries"),
    "insert_data_to_db": os.getenv('insert_data_to_db', "True").lower() == "true",
}

print("Environment variables:")
pprint.PrettyPrinter(indent=4).pprint(env_variables)


def main():
    import matplotlib.pyplot as plt
    import pandas as pd
    import timeSeriesL1Analytics
    from redis import Redis
    import json

    env_variables["filters"] = [env_variables["filters"]]
    # Check if Redis is up
    r = Redis(host=env_variables["redis_host"], port=env_variables["redis_port"])
    if not r.ping():
        print("Unable to reach redis timeseries at", env_variables["redis_host"], env_variables["redis_port"])
    start = time.time()
    # read time series from Redis
    all_data = timeSeriesFunctions.getDataFromRedis(host=env_variables["redis_host"],
                                                    port=env_variables["redis_port"],
                                                    from_time=env_variables["from_time"],
                                                    to_time=env_variables["to_time"],
                                                    aggregation_type=env_variables["aggregation_type"],
                                                    bucket_size_msec=env_variables["bucket_size_msec"],
                                                    filters=env_variables["filters"],
                                                    enablePercentChange=env_variables["enablePercentChange"])
    df = pd.DataFrame(all_data["df"])
    # Filter less interesting signals out
    df, df_lines, df_squares, df_spikes = timeSeriesFunctions.clusterTs(df)
    # Get regime changes and their histogram
    histogram, all_regimes = timeSeriesFunctions.getHistogramsFromMP(df,
                                                                     num_regimes=env_variables["num_regimes"],
                                                                     window=env_variables["window"])
    # Plot histogram of regime changes
    if env_variables["enablePlotting"]:
        plt.figure(0)
        plt.title("Histogram of Regime Changes")
        plt.bar(range(len(df)), histogram, width=3)
    events = timeSeriesL1Analytics.getCandidateEvents(histogram, len(df), env_variables["ts_freq_threshold"],
                                                      env_variables["peek_ratio"],
                                                      sampling_rate=all_data["ts_all"][0][1] - all_data["ts_all"][0][0])
    # Plot events on the histogram
    if env_variables["enablePlotting"]:
        plt.figure(1)
        plt.title("Histogram of Events")
        timeSeriesFunctions.plotEventsOnHistogram(histogram, len(df), events)
    # get indicators
    indicators = timeSeriesFunctions.getIndicators(events, df, all_regimes)
    # print event stats
    timeSeriesFunctions.printEventStats(all_data["ts_all"][0], indicators, events, env_variables["timeZone"])
    # Get predictive powers and generate correlations from a model
    df_event_contributor = pd.DataFrame()
    if env_variables["enablePrediction"]:
        df_event_contributor = timeSeriesFunctions.getBestPredictiveModel(events, df, all_regimes)
        # if len(df_event_contributor) > 0:
        #     df_plotly = df[list(df_event_contributor['li name'].values)].copy()
        #     timeSeriesFunctionsEdited.generateCorrelations(df_plotly, env_variables["enablePlotting"])
    # generate output
    redis_out = Redis(host=env_variables["output_redis_host"], port=env_variables["output_redis_port"])
    if redis_out.ping():
        output_data = {'events': events.to_dict(), 'indicators': indicators.to_dict(),
                       'contributors': df_event_contributor.to_dict()}
        output_data = json.dumps(output_data)
        _ = redis_out.xadd(env_variables["output_name"], {'data': output_data})
        _ = redis_out.execute_command("save")
    else:
        print("Unable to reach redis for output at", env_variables["output_redis_host"],
              env_variables["output_redis_port"])
    # Create dynamic dashboards
    timeSeriesFunctions.createDashBoards(events, indicators, df_event_contributor, all_data["ts_all"][0])
    print("SensorDog for TimeSeries Analysis completed in total of ", round(time.time() - start, 2), "sec.")


if __name__ == "__main__":
    if(env_variables["insert_data_to_db"]):
        print("Inserting data to db...")
        timeSeriesFunctions.loadDataToRedis(host=env_variables["redis_host"],
                                            port=env_variables["redis_port"],
                                            fname="20200712_Hawkeye.csv",
                                            labels={"TARGET": "SENSORDOG"})
        print("Done.")
        
    main()
    if(env_variables["enableBatch"] or env_variables["enableStreaming"]):
        redis_param=redis.Redis(host=env_variables["output_redis_host"],port=env_variables["output_redis_port"])
        print("enableMiniBatch or enableStreaming is True. Creating/setting SensorDog:param:killLoop = False on output Redis. Set it to True to kill this process after this loop.")
        _=redis_param.set('SensorDog:param:killLoop',"False")
        while(True):
            if(redis_param.exists("SensorDog:param:killLoop")):
                killLoop=bool(distutils.util.strtobool(redis_param.get('SensorDog:param:killLoop').decode('utf-8')))
                if(not killLoop):
                    if(not env_variables["enableStreaming"]):
                        print("sleeping until the next loop for", env_variables["process_period"],"sec. Set SensorDog:param:killLoop = True on output Redis to kill this process.")
                        time.sleep(env_variables["process_period"])
                    main()
                else:
                    print("killLoop signal received. Killing this process.")
                    exit
                
            
            
            
            
            
            
            
            
            
            
            