# -*- coding: utf-8 -*-
"""
SensorDog TimeSeries Analysis Main Functionality
"""

import argparse
import sys
from typing import List
import timeSeriesFunctions

def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--redis_host',
        type=str,
        default='localhost',
        help='redis host for input time series'
    )
    parser.add_argument(
        '--redis_port',
        type=int,
        default=6379,
        help='redis port for input time series'
    )
    parser.add_argument(
        '--output_redis_host',
        type=str,
        default='localhost',
        help='redis host for input time series'
    )
    parser.add_argument(
        '--output_redis_port',
        type=int,
        default=6379,
        help='redis port for input time series'
    )
    parser.add_argument(
        '--from_time',
        type=int,
        default=0,
        help='end of data analysis interval for time series. This is the larger one. 0 means now'
    )
    parser.add_argument(
        '--to_time',
        type=int,
        default=-1,
        help='start of data analysis interval for time series. This is the larger one. -1 means the oldest time stamps available'
    )
    parser.add_argument(
        '--aggregation_type',
        type=str,
        default='last',
        help='time series aggregation type (min, max, avg, first, last...)'
    )
    parser.add_argument(
        '--bucket_size_msec',
        type=int,
        default=60000,
        help='aggregation bucket size in msec for time series'
    )
    parser.add_argument(
        '--num_regimes',
        type=int,
        default=20,
        help='max number of semantic segmentation per time series for MP'
    )
    parser.add_argument(
        '--filters',
        type=str,
        default="TARGET=SENSORDOG",
        help='Filtering labels for redis mrange bulk reading'
    )
    parser.add_argument(
        '--ts_freq_threshold',
        type=int,
        default=50,
        help='threshold value for number of simultaneous regime changes for event detection'
    )
    parser.add_argument(
        '--peek_ratio',
        type=float,
        default=0.30,
        help='threshold value for peeks on histogram for event detection'
    )
    parser.add_argument(
        '--enablePlotting',
        default=True,
        help='Enable plotting of histograms and events.',
        action='store_true',
        dest='enablePlotting'
    )
    parser.add_argument(
        '--enablePrediction',
        default=True,
        help='Enable prediction based on event analysis.',
        action='store_true',
        dest='enablePrediction'
    )
    parser.add_argument(
        '--enablePercentChange',
        default=True,
        help='Enable using percent change in timeseries analysis instead of raw data.',
        action='store_true',
        dest='enablePercentChange'
    )
    parser.add_argument(
        '--window',
        type=int,
        default=10,
        help='window size for matrox profile algorithm'
    )
    parser.add_argument(
        '--timeZone',
        type=str,
        default='US/Pacific',
        help='time zone for timestamps'
    )
    parser.add_argument(
        '--output_name',
        type=str,
        default='SensorDog4TimeSeries',
        help='RedisStream variable name for outputing results'
    )

    return parser


def main(args: List[str])->None:
    from redistimeseries.client import Client
    import time
    import matplotlib.pyplot as plt
    import pandas as pd
    import timeSeriesL1Analytics
    from redis import Redis
    import json
    parser = get_cli_parser()
    cli_options = parser.parse_args(args)
    rts = Client(host=cli_options.redis_host, port=cli_options.redis_port)
    cli_options.filters=[cli_options.filters]
    #Check if Redis is up
    r=Redis(host=cli_options.redis_host, port=cli_options.redis_port)
    if(not r.ping()):
        print("Unable to reach redis timeseries at",cli_options.redis_host,cli_options.redis_port)
    start=time.time()
    #read time series from Redis
    all_data= timeSeriesFunctions.getDataFromRedis(host=cli_options.redis_host, port=cli_options.redis_port, from_time=cli_options.from_time,
                                                   to_time=cli_options.to_time, aggregation_type=cli_options.aggregation_type, bucket_size_msec=cli_options.bucket_size_msec, filters=cli_options.filters, enablePercentChange=cli_options.enablePercentChange)
    df=pd.DataFrame(all_data["df"])
    #Filter less interesting signals out
    df, df_lines,df_squares,df_spikes= timeSeriesFunctions.clusterTs(df)
    #Get regime changes and their histogram
    histogram, all_regimes= timeSeriesFunctions.getHistogramsFromMP(df, num_regimes=cli_options.num_regimes, window=cli_options.window)
    #Plot histogram of regime changes
    if(cli_options.enablePlotting):
        plt.figure(0)
        plt.title("Histogram of Regime Changes")
        plt.bar(range(len(df)),histogram,width=3)
    events= timeSeriesL1Analytics.getCandidateEvents(histogram, len(df), cli_options.ts_freq_threshold, cli_options.peek_ratio, sampling_rate=all_data["ts_all"][0][1] - all_data["ts_all"][0][0])
    #Plot events on the histogram
    if(cli_options.enablePlotting):
        plt.figure(1)
        plt.title("Histogram of Events")
        timeSeriesFunctions.plotEventsOnHistogram(histogram, len(df), events)
    #get indicators
    indicators= timeSeriesFunctions.getIndicators(events, df, all_regimes)
    #print evet stats
    timeSeriesFunctions.printEventStats(all_data["ts_all"][0], indicators, events, cli_options.timeZone)
    #Get predictive powers and generate correlations from a model
    df_event_contributor=pd.DataFrame()
    if(cli_options.enablePrediction):
        df_event_contributor= timeSeriesFunctions.getBestPredictiveModel(events, df, all_regimes)
        if(len(df_event_contributor)>0):
            df_plotly=df[list(df_event_contributor['li name'].values)].copy()
            timeSeriesFunctions.generateCorrelations(df_plotly, cli_options.enablePlotting)
    #generate output
    redis_out=Redis(host=cli_options.output_redis_host,port=cli_options.output_redis_port)
    if(redis_out.ping()):
        output_data={'events':events.to_dict(),'indicators':indicators.to_dict(),'contributors':df_event_contributor.to_dict()}
        output_data=json.dumps(output_data)
        _=redis_out.xadd(cli_options.output_name,{'data':output_data})
        _=redis_out.execute_command("save")
    else:
        print("Unable to reach redis for output at",cli_options.output_redis_host,cli_options.output_redis_port)
    #Create dynamic dashboards
    timeSeriesFunctions.createDashBoards(events, indicators, df_event_contributor, all_data["ts_all"][0])
    print("SensorDog for TimeSeries Analysis completed in total of ",round(time.time()-start,2),"sec.")
if __name__ == "__main__": 
    main(sys.argv[1:])
    #timeSeriesFunctions.loadDataToRedis(host='localhost',port=6379, fname="20200712_Hawkeye.csv",labels={"TARGET":"SENSORDOG"})











