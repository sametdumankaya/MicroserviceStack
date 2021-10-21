import pandas as pd
import time
import os
import datetime
import TimeSeriesEvents
import TimeSeriesL1Analytics
import matrixprofile as mp
import numpy as np
import matplotlib.pyplot as plt

def ingestHawkeyeData(data_dir="data",saveFile=True) -> pd.DataFrame:
    root_dir = os.getcwd() + '\\' +data_dir
    #import os
    #result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(root_dir) for f in filenames if os.path.splitext(f)[1] == '.txt']
    cnt=0
    tot_num_files = sum([len(files) for r, d, files in os.walk(root_dir)])
    df=pd.DataFrame(columns=['ts'])
    for subdir,dirs,files in os.walk(root_dir):
        rowIndex = len(df)
        if(len(files)>0): #First iteration is the root_dir itself. 
            tmp=subdir.split("\\")[-1].split("_")
            date=tmp[0][0:4]+"/"+tmp[0][4:6]+"/"+tmp[0][6:8]+ " " + tmp[1][0:2]+":"+tmp[1][2:4]+":"+tmp[1][4:6]
            date=datetime.datetime.strptime(date,"%Y/%m/%d %H:%M:%S")
            time_stamp = time.mktime(date.timetuple()) * 1000
            df.loc[rowIndex, 'ts'] = float(time_stamp)        
            for f in files:
                cnt=cnt+1
                df_file = pd.read_csv(subdir+"\\"+f, sep=' ', header=None, names=["n1", "counter", "n2","n3"])
                device=f.split(".")[0]
                counters=list(df_file["counter"].values)
                values=list(df_file["n2"].values.astype(float))
                counters = [device+":"+ item for item in counters]
                if(len(counters)!=len(values)):
                    print("mismatching numbers of counters and values in", subdir,f)
                    #return
                #df=addHawkeyeTstoDf(df,time_stamp,counters,values)
                for i in range(len(counters)):
                    col=counters[i]
                    val=values[i]
                    if(col not in df.columns):
                        df = df.reindex(df.columns.tolist() + [col], axis=1)
                    df.loc[rowIndex, col] = val 
                print(cnt,"/",tot_num_files)
    print(len(df.columns)-1, "counters with",len(df),"timestamps added")
    if(saveFile):
        df.to_csv(tmp[0]+'_Hawkeye.csv', header=True, index=False) 
    return df
if __name__ == "__main__": 
    data_dir="data"
    #start_all=time.time()
    #df=ingestHawkeyeData(data_dir=data_dir)
    #print(time.time()-start_all)
    #LOAD data and classify initial signals
    df=pd.read_csv("20200712_Hawkeye.csv")
    time_stamps=df.iloc[:,0].values
    df=df.drop(['ts'],axis=1)
    df,df_lines=TimeSeriesL1Analytics.filter_lines(df)
    df,df_spikes=TimeSeriesL1Analytics.filter_spikes(df)
    df_spquares,df_spikes=TimeSeriesL1Analytics.splitSquaresFromSpikes(df_spikes)
    
    #Matrix profile
    timings_mp=[]    
    timings_fluss=[]
    all_regimes=[]
    start_all=time.time()
    for i in range(len(df.columns)):
        ts=df.iloc[:,i]
        ts=ts[ts.notnull()].values.astype(np.float32)
        start_time = time.time()
        profile=mp.compute(ts,windows=[10])
        timings_mp.append(time.time()-start_time)
        start_time = time.time()
        x=mp.discover.regimes(profile, num_regimes=50)
        timings_fluss.append(time.time()-start_time)
        regimes= list(filter(lambda x: x != 0, x["regimes"]))
        regimes= list(filter(lambda x: x != len(df), regimes))
        all_regimes.append(regimes)
    print(time.time()-start_all)
    df_regimes=pd.DataFrame(all_regimes)
    date_time_stamps=[datetime.datetime.fromtimestamp(i/1000) for i in time_stamps]
    histogram=TimeSeriesEvents.getHistogramFromDf(df_regimes,len(df))
    plt.stem(date_time_stamps,histogram,markerfmt=" ")
    #plt.gcf().text(0.5, 0.5, "textstr", fontsize=6)
    plt.show()
    #filter some events
    filter_num=500
    event_count=[]
    event_timing=[]
    
    for i in range(len(histogram)):
        cnt=histogram[i]
        if(cnt>=500):
            event_count.append(cnt)
            event_timing.append(date_time_stamps[i])
    event_ts_names=[]
    for e in events:
        sub_list=[]
        ind=histogram.index(e)
        for i in range(len(all_regimes)):
            r=all_regimes[i]
            if(ind in r):
                sub_list.append(list(df.columns)[i])
        event_ts_names.append(sub_list)
    dict_hawkeye={"regimes":all_regimes, "ts":time_stamps,"analyzed_ts":analyzed_ts_names,"line_ts":line_ts_names,"square_wave_ts":square_wave_ts_names, "event_ts_names":event_ts_names}
    import pickle
    with open('dict_hawkeye.pickle', 'wb') as handle:
        pickle.dump(dict_hawkeye, handle, protocol=pickle.HIGHEST_PROTOCOL)    
        
            
    # x=df.iloc[:,1453]
    # x=x[x.notnull()].values.astype(np.float32)
    # profile, figures = mp.analyze(x, n_jobs=-1)
    # daily_profile = mp.utils.pick_mp(profile, 72)
    # daily_profile = mp.discover.discords(daily_profile, k=5, exclusion_zone=daily_window*7)
    # figures = mp.visualize(daily_profile)

    #plt.bar(range(len(df)),histogram)
    #plt.figure()    
    
    
    
    # dif=time_stamps[1]-time_stamps[0]
    # for i in range(2, len(time_stamps)):
    #     if(time_stamps[i]-time_stamps[i-1]!=dif):
    #         print(i)
    # analyzed_ts_names=list(df.columns)
    # line_ts_names=list(df_lines)
    # square_wave_ts_names=list(df_spquares)
    
    # time_stamps=time_stamps.astype(np.float32)

    
    # with open('dict_hawkeye.pickle', 'rb') as handle:
    #      b = pickle.load(handle)