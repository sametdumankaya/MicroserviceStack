from redistimeseries.client import Client
import pandas as pd
import time
import os
import argparse
import sys
import os.path

def get_cli_parser() -> argparse.ArgumentParser:
    parent_path=os.path.abspath(os.path.join(__file__,"../.."))
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ## Help0  cli_parser.add_argument('--title', nargs='?', const='dfre2grafana', type=str)
    cli_parser.add_argument('--input', nargs='?', const=parent_path+'\\merged_191015_1949.csv', default=parent_path+'\\merged_191015_1949.csv',type=str,dest='input',action='store')
    cli_parser.add_argument('--redis_host', nargs='?', const='localhost', default='localhost',type=str,dest='redis_host',action='store')
    cli_parser.add_argument('--redis_port', nargs='?', const=6380, default=6380,type=int,dest='redis_port',action='store')
    cli_parser.add_argument('--isMilliSeconds',default= True, action='store_true', dest='isMilliSeconds')
    return cli_parser

def loadTsData(df:pd.DataFrame,redis_host_ip:str,redis_port:int,isMilliSeconds=True):
    """ 
        This function receives a dataframe of time series whose first column is ts, and
        loads the data into redis time series. If the timestamps are in millisconds, it will be multiplied by 1000.
        Set isMilliSeconds=False if your stamps are already in unix timestamps microsecs
    """
    rts = Client(host=redis_host_ip, port=redis_port)
    #NOTE: .astype(int) function of pandas returns int32 or int64 which causes error in redistimeserier. 
    #Use default int type casting instead.
    timeStamps=df.iloc[:,0].values.astype(float)
    if(isMilliSeconds):
        timeStamps*=1000
    timeStamps=[int(x) for x in timeStamps]
    for i in range(1, len(df.columns)):
        ts_name='ts'+str(i)
        ts_label=df.columns[i]
        #Create time series
        """naming conventions"""
        try:
            rts.create(ts_name, labels={'full_name':ts_label,'l2category':' ','source':' '})
        except:
            rts.delete(ts_name)
            rts.create(ts_name, labels={'full_name':ts_label,'l2category':' ','source':' '})
        #Create array of key, ts, value tuples
        arr_ktv=tuple(zip(timeStamps, df.iloc[:,i].values.astype(float)))
        arr_ktv=[(ts_name,)+xs for xs in arr_ktv]
        _=rts.madd(arr_ktv)
    return

def streamTsData(df:pd.DataFrame,redis_host_ip:str,redis_port:int,isMilliSeconds=True):
    rts = Client(host=redis_host_ip, port=redis_port)
    tsNames=[]
    df=df.drop(['ts'], axis=1)
    ms2mc=1
    if(isMilliSeconds):ms2mc=1000
    #Delete the existing ts
    for i in range(1, len(df.columns)):
        ts_label=str(df.columns[i])
        ts_name= ts_name='ts'+str(i)
        try:
            rts.create(ts_name, labels={'full_name':ts_label,'l2category':' ','source':' '})
            tsNames.append(ts_name)
        except:
            rts.delete(ts_name)
            rts.create(ts_name, labels={'full_name':ts_label,'l2category':' ','source':' '})
            tsNames.append(ts_name)
    while(True):
        for i in range(len(df)):
            data=df.iloc[i,:].values.astype(float)
            timestamps=[round(time.time()*ms2mc)]*len(data)
            merged_data=list(zip(tsNames,timestamps,data))
            _=rts.madd(merged_data)
        

if __name__ == "__main__":
    argv=sys.argv[1:]
    cli_parser = get_cli_parser()
    cli_options = cli_parser.parse_args(argv)
    fname=cli_options.input
    redis_host=cli_options.redis_host
    redis_port=cli_options.redis_port
    df=pd.read_csv(fname)
    isMilliSeconds=cli_options.isMilliSeconds
    streamTsData(df,redis_host,redis_port,isMilliSeconds)
    
  

    