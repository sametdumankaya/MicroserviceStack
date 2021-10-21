import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import TimeSeriesEvents
import MSig_Functions as MSig
import sys,os
import argparse
from typing import List
import redis
import threading

MSIG_OUTPUT="msig:output"
if "MSIG_MYSQL_PASS" in os.environ:
    MSIG_MYSQL_PASS=os.environ["MSIG_MYSQL_PASS"]
else:
    print("Unable to read environment variable MSIG_MYSQL_PASS...")
    MSIG_MYSQL_PASS=""
_=np.seterr(all="ignore")
def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--period',
        type=int,
        default=600,
        help="period of signal processing in sec. 300 --> analyze data for every 5 min."
    )
    parser.add_argument(
        '--L2fileName',
        type=str,
        default='finL2Extension.graphml',
        help='L2 file for symbols and company names'
    )
    parser.add_argument(
        '--redis_host',
        type=str,
        default='localhost',
        help='redis host for input time series'
    )
    parser.add_argument(
        '--redis_port',
        type=int,
        default=6381,
        help='redis port for input time series'
    )
    parser.add_argument(
        '--msig_host',
        type=str,
        default='localhost',
        help='redis host for signal output'
    )
    parser.add_argument(
        '--msig_port',
        type=int,
        default=6379,
        help='redis port for signal output'
    )
    parser.add_argument(
        '--mind_host',
        type=str,
        default='localhost',
        help='redis host for index output'
    )
    parser.add_argument(
        '--mind_port',
        type=int,
        default=6378,
        help='redis port for index output'
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
        '--prefix',
        type=str,
        default='rts1:01:',
        help='prefix of the keys of interest on redis'
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
        '--window_size',
        type=int,
        default=10,
        help='window size fr semantic segmentation of time series for MP. When MP disabled, this is the parameter for percent-change-based gain and loss index.'
    )
    parser.add_argument(
        '--last_batch_control_variable',
        type=str,
        default="mac_simlooping",
        help='this variable marks if this is end'
    )
    parser.add_argument(
        '--filters',
        type=str,
        default="SYMSET=ACTIVE_VOLUME,SYMSET=ACTIVE_PRICE",
        help='Filtering labels for redis mrange bulk reading'
    )
    parser.add_argument(
        '--ts_freq_threshold',
        type=int,
        default=20,
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
        default=False,
        help='Enable plotting of histograms and events.',
        action='store_true',
        dest='enablePlotting'
    )
    parser.add_argument(
        '--killMSig',
        default=False,
        help='Signal to kill MSig.',
        action='store_true',
        dest='killMSig'
    )
    parser.add_argument(
        '--enableSectorIndustry',
        default=True,
        help='Enable sector and industry-based anaysis of events.',
        action='store_false',
        dest='enableSectorIndustry'
    )
    parser.add_argument(
        '--enablePrediction',
        default=False,
        help='Enable prediction based on event analysis.',
        action='store_true',
        dest='enablePrediction'
    )
    parser.add_argument(
        '--enableNewsGeneration',
        default=True,
        help='Enable news generation based on event analysis.',
        action='store_false',
        dest='enableNewsGeneration'
    )
    parser.add_argument(
        '--saveToMysql',
        default=True,
        help='Enable to save session info and events to MYSql.',
        action='store_false',
        dest='saveToMysql'
    )
    parser.add_argument(
        '--mysql_port',
        type=int,
        default=3307,
        help='mysql port for signal output'
    )
    parser.add_argument(
        '--mysql_host',
        type=str,
        default='127.0.0.1',
        help='mysql host for signal output'
    )
    parser.add_argument(
        '--mysql_user',
        type=str,
        default='root',
        help='mysql user for signal output'
    )
    parser.add_argument(
        '--mysql_db',
        type=str,
        default='msig',
        help='mysql database for signal output'
    )
    parser.add_argument(
        '--mysql_pass',
        type=str,
        default=MSIG_MYSQL_PASS,
        help='mysql password for signal output. Default is set to the environment variable $MSIG_MYSQL_PASS'
    )
    parser.add_argument(
        '--enableMP',
        default=False,
        help='Enable using matrix profile based event generation. When disabled, gain loss indices are used.',
        action='store_true',
        dest='enableMP'
    )
    parser.add_argument(
        '--isLive',
        default=True,
        help='Parameter to make sure this port is love data port',
        action='store_false',
        dest='isLive'
    )
    parser.add_argument(
        '--enableCorrelations',
        default=True,
        help='Enable pushing correlation plots to the front end. Event correlations are pushed at each computation. Industries are daily',
        action='store_false',
        dest='enableCorrelations'
    )
    parser.add_argument(
        '--gainLossEventRatio',
        type=float,
        default=0.05,
        help='If a peak\'s height is grater/smaller than this ratio, it is an event' 
    )
    parser.add_argument(
        '--gainLossIndicatorThreshold',
        type=float,
        default=0.025,
        help='If a company\'s gain/loss is larger/smaller than this ratio, it is an indicator of that event' 
    )
    parser.add_argument(
        '--timeZone',
        type=str,
        default='US/Pacific',
        help='Time zone of the context' 
    )
    parser.add_argument(
        '--curatedNews',
        type=str,
        default='USA Political, Bitcoin, Covid-19',
        help='Topics for curated news' 
    )
    return parser

#MAIN LOOP
def main(args: List[str],isLoopOnce=False) -> None:
    import json
    import distutils
    from datetime import datetime, timedelta
    import time
    import pytz
    year=0
    month=0
    hour=0
    day=0
    minute=0
    x=datetime.today()
    isStartofDay=False
    parser = get_cli_parser()
    cli_options = parser.parse_args(args)
    cli_options.window_size=[cli_options.window_size]
    #cli_options.filters=[cli_options.filters]
    is_system_start=True   
    process_period=cli_options.period
    redis_msig=redis.Redis(host=cli_options.msig_host,port=cli_options.msig_port)
    #SIGNAL GENERATION LOOP
    loop_num=0
    msig_clock=time.time()
    while(True):
        #Set or read default parameters from/to msig_redis
        if(is_system_start):
            #TODO: Add all parameters here for dynamic controlling
            print("1. LOOP BEGINS. Keep an eye on 'msig' database @ mysql...")
            _=redis_msig.set('msig:param:period',int(cli_options.period)) #Event detection period
            _=redis_msig.set('msig:param:num_regimes',int(cli_options.num_regimes)) #number of max regime changes
            _=redis_msig.set('msig:param:window_size',str(cli_options.window_size).encode('utf-8')) #window size for sem seg
            _=redis_msig.set('msig:param:peek_ratio',cli_options.peek_ratio) #Peek ratio for event detection on histograms
            _=redis_msig.set('msig:param:ts_freq_threshold',cli_options.ts_freq_threshold) #Threshold value for num of reg changes for event detection on histograms
            _=redis_msig.set('msig:param:enableSectorIndustry',str(cli_options.enableSectorIndustry)) #Bool var if sector and industry analysis is required
            _=redis_msig.set('msig:param:bucket_size_msec',int(cli_options.bucket_size_msec)) #aggregation bucket size
            _=redis_msig.set('msig:param:aggregation_type',str(cli_options.aggregation_type)) #aggregation type
            _=redis_msig.set('msig:param:enableCorrelations',str(cli_options.enableCorrelations)) #aggregation bucket size
            _=redis_msig.set('msig:param:enableMP',str(cli_options.enableMP)) #aggregation bucket size
            _=redis_msig.set('msig:param:enableNewsGeneration',str(cli_options.enableNewsGeneration)) #aggregation bucket size
            _=redis_msig.set('msig:param:enablePlotting',str(cli_options.enablePlotting)) #aggregation bucket size
            _=redis_msig.set('msig:param:enablePrediction',str(cli_options.enablePrediction)) #aggregation bucket size
            _=redis_msig.set('msig:param:enableSectorIndustry',str(cli_options.enableSectorIndustry)) #aggregation bucket size
            _=redis_msig.set('msig:param:from_time',int(cli_options.from_time)) #aggregation bucket size
            _=redis_msig.set('msig:param:to_time',int(cli_options.to_time)) #aggregation bucket size
            _=redis_msig.set('msig:param:gainLossEventRatio',cli_options.gainLossEventRatio) #aggregation bucket size
            _=redis_msig.set('msig:param:gainLossIndicatorThreshold',cli_options.gainLossIndicatorThreshold) #aggregation bucket size
            _=redis_msig.set('msig:param:saveToMysql',str(cli_options.saveToMysql)) 
            _=redis_msig.set('msig:param:killMSig',str(cli_options.killMSig)) 
            _=redis_msig.set('msig:param:isLive',str(cli_options.isLive)) 
            _=redis_msig.set('msig:param:curatedNews',str(cli_options.curatedNews)) 
            loop_num=loop_num+1
        else:
            cli_options.period=int(redis_msig.get('msig:param:period'))
            cli_options.num_regimes=int(redis_msig.get('msig:param:num_regimes'))
            cli_options.window_size=list(map(int,redis_msig.get('msig:param:window_size').decode('utf-8')[1:-1].split(',')))
            cli_options.peek_ratio=float(redis_msig.get('msig:param:peek_ratio'))
            cli_options.ts_freq_threshold=int(redis_msig.get('msig:param:ts_freq_threshold'))
            cli_options.enableSectorIndustry=bool(distutils.util.strtobool(redis_msig.get('msig:param:enableSectorIndustry').decode('utf-8')))
            cli_options.bucket_size_msec=int(redis_msig.get('msig:param:bucket_size_msec'))
            cli_options.aggregation_type=str(redis_msig.get('msig:param:aggregation_type').decode('utf-8'))
            cli_options.enableCorrelations=bool(distutils.util.strtobool(redis_msig.get('msig:param:enableCorrelations').decode('utf-8')))
            cli_options.enableMP=bool(distutils.util.strtobool(redis_msig.get('msig:param:enableMP').decode('utf-8')))
            cli_options.enableNewsGeneration=bool(distutils.util.strtobool(redis_msig.get('msig:param:enableNewsGeneration').decode('utf-8')))
            cli_options.enablePlotting=bool(distutils.util.strtobool(redis_msig.get('msig:param:enablePlotting').decode('utf-8')))
            cli_options.enablePrediction=bool(distutils.util.strtobool(redis_msig.get('msig:param:enablePrediction').decode('utf-8')))
            cli_options.enableSectorIndustry=bool(distutils.util.strtobool(redis_msig.get('msig:param:enableSectorIndustry').decode('utf-8')))
            cli_options.from_time=int(redis_msig.get('msig:param:from_time'))
            cli_options.to_time=int(redis_msig.get('msig:param:to_time'))
            cli_options.gainLossEventRatio=float(redis_msig.get('msig:param:gainLossEventRatio'))
            cli_options.gainLossIndicatorThreshold=float(redis_msig.get('msig:param:gainLossIndicatorThreshold'))
            cli_options.saveToMysql=bool(distutils.util.strtobool(redis_msig.get('msig:param:saveToMysql').decode('utf-8')))
            cli_options.killMSig=bool(distutils.util.strtobool(redis_msig.get('msig:param:killMSig').decode('utf-8')))
            cli_options.isLive=bool(distutils.util.strtobool(redis_msig.get('msig:param:isLive').decode('utf-8')))
            cli_options.curatedNews=redis_msig.get('msig:param:curatedNews').decode('utf-8')
            if(cli_options.killMSig):
                print("Kill signal received")
                print("Bye!")
                _=redis_msig.set('msig:param:killMSig','False') 
                return
            x=datetime.today()
            year=x.year
            month=x.month
            day=x.day
            hour=x.hour
            minute=x.minute
            weekday=x.weekday()
            if(weekday==5):#saturday
                future=datetime(x.year, x.month, x.day,6,41)+timedelta(days=2)
                print("Don't kill me yet. Wait for the Thread to send 'Done' signal!\n")
                print("Market is not open. Sleeping until ",future)
                time.sleep((future-x).total_seconds())
                isStartofDay=True
            elif(weekday==6):#sunday
                future=datetime(x.year, x.month, x.day,6,41)+timedelta(days=1)
                print("Don't kill me yet. Wait for the Thread to send 'Done' signal!\n")
                print("Market is not open. Sleeping until ",future)
                time.sleep((future-x).total_seconds())
                isStartofDay=True
            else:#weekdays
                if(hour<6 or (hour==6 and minute<41)):
                    future=datetime(x.year, x.month, x.day,6,41)
                    print("Market is not open. Sleeping until ",future)
                    print("Don't kill me yet. Wait for the Thread to send 'Done' signal!\n")
                    time.sleep((future-x).total_seconds())
                    isStartofDay=True
                elif(hour>13 or (hour==13 and minute>15)):
                    if(weekday==4):#friday, sleep 2 days
                        future=datetime(x.year, x.month, x.day,6,41)+timedelta(days=3)
                    else:#other weekdays sleep 1 day
                        future=datetime(x.year, x.month, x.day,6,41)+timedelta(days=1)
                    print("Market is closed. Sleeping until ",future)
                    print("Don't kill me yet. Wait for the Thread to send 'Done' signal!\n")
                    time.sleep((future-x).total_seconds())
                    isStartofDay=True
        #If this is the first processing or we have waited long enough for process_period, repeat
        if(is_system_start or time.time()-msig_clock>=process_period):
            start=time.time()
            if(not(is_system_start)):
                loop_num+=1
                print(loop_num, ". LOOP BEGINS:")
            is_system_start=False
            
            while(True):#Try reading data from mrF
                try:
                    all_data=MSig.get_data_from_mrF(redis_host=cli_options.redis_host,redis_port=cli_options.redis_port,
                                         from_time=cli_options.from_time,to_time=cli_options.to_time,
                                         query_key=None,prefix=cli_options.prefix,
                                         aggregation_type=cli_options.aggregation_type,bucket_size_msec=\
                                         cli_options.bucket_size_msec,last_batch_control_variable=cli_options.last_batch_control_variable,filters=cli_options.filters)
                    
                    # if(len(all_data)>0):
                    #     if(cli_options.isLive):
                    #         tmp_date=datetime.fromtimestamp(all_data['ts_price_min']/1000).astimezone(pytz.timezone(cli_options.timeZone))
                    #         if(tmp_date.year != year or tmp_date.year != month or tmp_date.year != day):
                    #             print("Data belongs to", tmp_date.strftime("%Y-%m-%d"),". Today is",x.strftime("%Y-%m-%d"))
                    #             print("Either disable isLive parameter or check your data on Redis.TERMINATING...")
                    #             return
                    break
                except Exception as e:
                    print(e)
                    print("sleeping for",process_period,"sec. before trying again")
                    time.sleep(process_period)
                    
            if(cli_options.enableMP):
                print("Using Matrix Profile algorithm...")
                #GET REGIME CHANGES
                print("Performing semantic segmentation of prices...")
                df_regimes_price=MSig.get_regime_changes(all_data["df_price_data"],num_regimes=cli_options.num_regimes,windows=cli_options.window_size[0])
                print("Performing semantic segmentation of volumes...")
                df_regimes_volume=MSig.get_regime_changes(all_data["df_volume_data"],num_regimes=cli_options.num_regimes,windows=cli_options.window_size[0])
                #GET HISTOGRAMS
                print("Producing histogram of regime changes for prices...")
                histogram_price=MSig.getHistogramFromUnalignedDf(df_regimes_price,all_data["ts_price"],all_data["ts_price_min"],all_data["ts_price_max"],cli_options.bucket_size_msec,window_size=cli_options.window_size[0])
                print("Producing histogram of regime changes for volumes...")
                histogram_volume=MSig.getHistogramFromUnalignedDf(df_regimes_volume,all_data["ts_volume"],all_data["ts_volume_min"],all_data["ts_volume_max"],cli_options.bucket_size_msec,window_size=cli_options.window_size[0])
                #Plotting
                all_ts_price=list(range(all_data["ts_price_min"], all_data["ts_price_max"]+cli_options.bucket_size_msec,cli_options.bucket_size_msec))
                date_time_stamps=[datetime.fromtimestamp(i/1000) for i in all_ts_price]
                if(cli_options.enablePlotting):
                    print("Attempting to plot histograms visually...")
                    plt.title("Histogram of price regime changes")
                    markerline, stemlines, baseline = plt.stem(date_time_stamps,histogram_price,markerfmt=" ")
                    plt.figure()
                all_ts_volume=list(range(all_data["ts_volume_min"], all_data["ts_volume_max"]+cli_options.bucket_size_msec,cli_options.bucket_size_msec))
                date_time_stamps=[datetime.fromtimestamp(i/1000) for i in all_ts_volume]
                if(cli_options.enablePlotting):
                    plt.title("Histogram of volume regime changes")
                    markerline, stemlines, baseline = plt.stem(date_time_stamps,histogram_volume,markerfmt=" ")
                #Detect events
                events_price=TimeSeriesEvents.getCandidateEvents(histogram_price,len(all_ts_price),ts_freq_threshold=cli_options.ts_freq_threshold,peek_ratio=cli_options.peek_ratio,sampling_rate=cli_options.bucket_size_msec)
                events_volume=TimeSeriesEvents.getCandidateEvents(histogram_volume,len(all_ts_volume),ts_freq_threshold=cli_options.ts_freq_threshold,peek_ratio=cli_options.peek_ratio,sampling_rate=cli_options.bucket_size_msec)
                print(events_price)
                print(events_volume)
                #plot events
                if(cli_options.enablePlotting):
                    print("Attempting to plot events visually ...")
                    p1=MSig.plotMSigEvents(len(all_ts_price),histogram_price,events_price,"Price Events",cli_options.bucket_size_msec)
                    p1.figure()
                    p2=MSig.plotMSigEvents(len(all_ts_volume),histogram_volume,events_volume,"Volume Events",cli_options.bucket_size_msec)
                    p2.show()
                #indicators
                #all_data["ts_volume_min"], all_data["ts_volume_max"]
                indicators_price=MSig.getIndicators(all_data,events_price,df_regimes_price,all_data["ts_price_min"],all_data["ts_price_max"],"ts_price","df_price_data",cli_options.bucket_size_msec)
                indicators_volume=MSig.getIndicators(all_data,events_volume,df_regimes_volume,all_data["ts_volume_min"],all_data["ts_volume_max"],"ts_volume","df_volume_data",cli_options.bucket_size_msec)
                #get market capitals per event
                df_market_capital_price=MSig.getMarketCapitalPerEvent(all_ts_price,all_data,events_price,indicators_price)
                df_market_capital_volume=MSig.getMarketCapitalPerEvent(all_ts_volume,all_data,events_volume,indicators_volume)
            else:
                if(len(all_data)==0):
                    print("There is no data to process from Mr. F")
                    return
                print("Calculating events & indicators based on gain/loss")
                isThreadRunning=True
                sleep_count=0
                while(isThreadRunning):
                    try:
                        sleep_count=sleep_count+1
                        events_price_gain,events_price_loss, events_volume_gain, events_volume_loss,indicators_price_gain,indicators_price_loss, indicators_volume_gain, indicators_volume_loss=MSig.getEventsFromGainLoss(all_data,cli_options.window_size[0],cli_options.enablePlotting,cli_options.gainLossEventRatio,cli_options.gainLossIndicatorThreshold,cli_options.mind_host,cli_options.mind_port,cli_options.bucket_size_msec,all_data["ts_price_min"],cli_options.prefix,cli_options.L2fileName)                                               
                        isThreadRunning=False
                        if(sleep_count==5):isThreadRunning=False
                    except Exception as e:
                        print(e)
                        print("sleeping for 30 seconds to make sure thread safe")
                        time.sleep(30)
                all_ts_price=list(range(all_data["ts_price_min"], all_data["ts_price_max"]+cli_options.bucket_size_msec,cli_options.bucket_size_msec))
                df_market_capital_price_gain=MSig.getMarketCapitalPerEvent(all_ts_price,all_data,events_price_gain,indicators_price_gain)
                df_market_capital_price_loss=MSig.getMarketCapitalPerEvent(all_ts_price,all_data,events_price_loss,indicators_price_loss)
                all_ts_volume=list(range(all_data["ts_volume_min"], all_data["ts_volume_max"]+cli_options.bucket_size_msec,cli_options.bucket_size_msec))
                df_market_capital_volume_gain=MSig.getMarketCapitalPerEvent(all_ts_volume,all_data,events_volume_gain,indicators_volume_gain)
                df_market_capital_volume_loss=MSig.getMarketCapitalPerEvent(all_ts_volume,all_data,events_volume_loss,indicators_volume_loss)
                print("Numbers for events_price_gain={},events_price_loss={}, events_volume_gain={}, events_volume_loss={}".format(len(events_price_gain),len(events_price_loss),len(events_volume_gain),len(events_volume_loss)))
                events_price=pd.concat([events_price_gain,events_price_loss],axis=0).reset_index(drop=True)
                events_volume=pd.concat([events_volume_gain,events_volume_loss],axis=0).reset_index(drop=True)
                indicators_price=pd.concat([indicators_price_gain,indicators_price_loss],axis=0).reset_index(drop=True)
                indicators_volume=pd.concat([indicators_volume_gain,indicators_volume_loss],axis=0).reset_index(drop=True)
                if(len(df_market_capital_price_gain)>0 and len(df_market_capital_price_loss)>0):
                    df_market_capital_price_loss["event_number"]+=max(df_market_capital_price_gain["event_number"])
                df_market_capital_price=pd.concat([df_market_capital_price_gain,df_market_capital_price_loss],axis=0).reset_index(drop=True)
                if(len(df_market_capital_volume_gain)>0 and len(df_market_capital_volume_loss)>0):
                    df_market_capital_volume_loss["event_number"]+=max(df_market_capital_volume_gain["event_number"])
                df_market_capital_volume=pd.concat([df_market_capital_volume_gain,df_market_capital_volume_loss],axis=0).reset_index(drop=True)

            #sector industry analysis
            df_sectors_price=pd.DataFrame()
            df_industries_price=pd.DataFrame()
            df_sectors_volume=pd.DataFrame()
            df_industries_volume=pd.DataFrame()
            if(cli_options.enableSectorIndustry):
                print("Analyzing sectors and industries ...")
                df_sectors_price,df_industries_price=MSig.getSectorIndustryPerEvent(indicators_price,"finL2Extension.graphml")
                df_sectors_volume,df_industries_volume=MSig.getSectorIndustryPerEvent(indicators_volume,"finL2Extension.graphml")

            #Send signal data to Redis
            print("Preparing data for News generation and MSig database...")
            msig_data={"loop_num":loop_num,"ts_price":all_data["ts_price"],"ts_volume":all_data["ts_volume"],\
                        "events_price":events_price,"events_volume":events_volume,\
                        "indicators_price":indicators_price,"indicators_volume":indicators_volume,\
                        "df_sectors_price":df_sectors_price,"df_industries_price":df_industries_price,\
                        "df_sectors_volume":df_sectors_volume,"df_industries_volume":df_industries_volume,\
                        "df_market_capital_price":df_market_capital_price,"df_market_capital_volume":df_market_capital_volume, \
                        "ts_price_min":all_data["ts_price_min"],"ts_price_max":all_data["ts_price_max"],"ts_volume_min":all_data["ts_volume_min"],"ts_volume_max":all_data["ts_volume_max"]}
            #_=redis_msig.rpush(MSIG_OUTPUT,pickle.dumps(msig_data))
            if(len(events_price)>0 or len(events_volume)>0):
                #TODO! sendToMYsql is slow. work on optimizing it.
                 #Generate news signal
                if(cli_options.enableNewsGeneration):
                    print("Generating news...")
                    try:
                        MSig.sendNewsToFrontEnd(msig_data,cli_options,df_market_capital_price,df_market_capital_volume,num_events_price_gain=len(events_price_gain),num_events_volume_gain=len(events_volume_gain),isStartofDay=isStartofDay)
                        print("Done")
                    except Exception as e:
                        print(e)
                if(cli_options.saveToMysql):
                    try:
                        event_price_ids,event_volume_ids=MSig.sendToMysql(msig_data,cli_options.mysql_host,cli_options.mysql_port,cli_options.mysql_db,cli_options.mysql_user,cli_options.mysql_pass)
                    except Exception as e:
                        print(e)
                        pass
                else:
                    event_price_ids=[]
                    event_volume_ids=[]
                     #Generate prediction signal
                if(cli_options.enablePrediction):
                    print("Triggering MModel for predictive models based on this batch...")
                    mmodel_data={"events_price":events_price.to_dict(),"events_volume":events_volume.to_dict(),"event_volume_ids":event_volume_ids,\
                             "event_price_ids":event_price_ids,"price_columns":list(all_data["df_price_data"].columns),\
                             "volume_columns":list(all_data["df_volume_data"].columns), "regimes_price":df_regimes_price.to_dict(),\
                              "regimes_volume":df_regimes_volume.to_dict(),"ts_price_min":all_data["ts_price_min"],"ts_price_max":all_data["ts_price_max"],"ts_volume_min":all_data["ts_volume_min"],\
                           "bucket_size_msec": cli_options.bucket_size_msec,"ts_volume_max":all_data["ts_volume_max"]}
                    mmodal_data_serial=json.dumps(mmodel_data)
                    _=redis_msig.xadd(MSIG_OUTPUT,{'data':mmodal_data_serial})
            else:
                print("No events detected... Not enough data...")
            msig_clock=time.time()
            end_time=time.time()
            if((len(events_price)>0 or len(events_volume)>0) and cli_options.saveToMysql):
                print("Saving the session parameters...")
                MSig.saveSessionInfo(event_price_ids,event_volume_ids,cli_options,start*1000,end_time*1000)
            print(loop_num, ". loop took",end_time-start,"sec. Not bad?")

        else:
            if(isLoopOnce):return
            is_system_start=False
            print("Sleeping until the next period starts in",process_period,"sec. Now your chance to change any parameters on msig redis. Don't kill me if parallel threads are running.\n")
            print("Don't kill me yet. Wait for the Thread to send 'Done' signal!\n")
            time.sleep(process_period)
        

if __name__ == "__main__":
    main(sys.argv[1:])
#    import pickle
#    outfile=open("all_data",'wb')
#    pickle.dump(all_data,outfile)
#    outfile.close()
#####
    # ports=[item for item in range(6400,6470)]
    # for p in ports:
    #     args=["--redis_port",str(p)]
    #     main(args,isLoopOnce=True)
    #     print(p,"Done")


#redis_msig.delete(MSIG_OUTPUT)

#x=rts.lrange("msig:output",0,-1)
#rdcli -h localhost -p 6380
#ssh -L 6379:localhost:6379 ubuntu@34.223.57.176 -i $HOME\.ssh\bastion1.pem
#ssh -L 6379:localhost:6379 ubuntu@34.223.57.176 -i ~/.ssh/bastion1.pem
#ssh -L 6380:localhost:6380 ubuntu@34.223.57.176 -i ~/.ssh/bastion1.pem
# from redistimeseries.client import Client
# rts = Client(host='localhost', port=6380)

# result=rts.range('rts1:01:symbol:BLKB:price', 0, -1)
