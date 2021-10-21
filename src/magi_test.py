
#rdcli -h localhost -p 6380
#ssh -L 6380:localhost:6379 ubuntu@34.223.57.176 -i $HOME\.ssh\bastion1.pem

# from redistimeseries.client import Client
# rts = Client(host='localhost', port=6380)

# result=rts.range('rts1:01:symbol:BLKB:price', 0, -1)

# import redis
# r = redis.Redis(port=6380)
# response=r.execute_command("keys *")

import time
import pandas as pd
import matplotlib.pyplot as plt
import matrixprofile as mp
from datetime import datetime
import numpy as np
import TimeSeriesEvents
import TimeSeriesL1Analytics
def get_ssh_connection(host=None, username=None,identity_file_name=None):
    import paramiko
    import os
    try:
        if(host==None):
            host=os.getenv("BASTION_HOST")
        if(username==None):
            username=os.getenv("BASTION_USER")
        if(identity_file_name==None):
            identity_file_name=os.getenv("BASTION_FILENAME")
        if(host==None or username==None or identity_file_name==None):
            print("Cannot read environment variables (BASTION_HOST, BASTION_USER, BASTION_FILENAME) for ssh connection")
            return None
    except Exception as e:
        print(e)
        return None
    try:
        cert = paramiko.RSAKey.from_private_key_file(identity_file_name)
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect( hostname = host, username = username, pkey = cert)
        return c
    except Exception as e:
        print(e)
        return None
    
def get_data_from_mrF(host="localhost",port=6380,from_date=0,to_date=-1,key=None,prefix='rts1:01:',aggregation_type="last",bucket_size_msec=1000):
    import redis
    from tqdm import tqdm
    r = redis.Redis(host=host,port=port)
    from redistimeseries.client import Client
    rts = Client(host=host, port=port)
    ts_price=[]
    data_price=[]
    ts_volume=[]
    data_volume=[]
    keys_price=[]
    keys_volume=[]
    ts_price_min=[]
    ts_volume_min=[]
    ts_price_max=[]
    ts_volume_max=[]
    #keyset_price=""
    #keyset_volume=""
    from_date=int(from_date)
    to_date=int(to_date)
    try:
        if(key==None):
            all_keys=r.execute_command("keys *")
            pbar=tqdm(total=len(all_keys),position=0)
            for k in all_keys:
                k=k.decode("utf-8")
                if(prefix in k and "price" in k):
                    x=rts.range(k, from_date, to_date,aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec)
                    ts,data = map(list,zip(*x))
                    ts_price_min.extend(ts)
                    ts_price_min=[min(ts_price_min)]
                    ts_price_max.extend(ts)
                    ts_price_max=[max(ts_price_max)]
                    ts_price.append(ts)
                    data_price.append(data)
                    keys_price.append(k.split(":")[3])
                elif(prefix in k and "volume" in k):
                    x=rts.range(k, from_date, to_date,aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec)
                    ts,data = map(list,zip(*x))
                    ts_volume_min.extend(ts)
                    ts_volume_min=[min(ts_volume_min)]
                    ts_volume_max.extend(ts)
                    ts_volume_max=[max(ts_volume_max)]
                    ts_volume.append(ts)
                    data_volume.append(data)
                    keys_volume.append(k.split(":")[3])
                pbar.update(1)
    except Exception as e:
        print(e)
    df_price_data=pd.DataFrame(data_price)
    df_price_data=df_price_data.transpose()
    df_price_data.columns=keys_price
    
    df_volume_data=pd.DataFrame(data_volume)
    df_volume_data=df_volume_data.transpose()
    df_volume_data.columns=keys_volume
    all_data={"ts_price":ts_price,"df_price_data":df_price_data,"ts_price_min":ts_price_min[0],"ts_price_max":ts_price_max[0],"ts_volume":ts_volume,"df_volume_data":df_volume_data,"ts_volume_min":ts_volume_min[0],"ts_volume_max":ts_volume_max[0]}
    return all_data

def get_regime_changes(df,num_regimes=50,windows=[10]):
    from tqdm import tqdm
     #Matrix profile
    timings_mp=[]    
    timings_fluss=[]
    all_regimes=[]
    start_all=time.time()
    pbar=tqdm(total=len(df.columns),position=0)
    for i in range(len(df.columns)):
        ts=df.iloc[:,i]
        ts=ts[ts.notnull()].values.astype(np.float32)
        start_time = time.time()
        profile=mp.compute(ts,windows=windows)
        timings_mp.append(time.time()-start_time)
        start_time = time.time()
        
        try:
            x=mp.discover.regimes(profile, num_regimes=num_regimes)
            timings_fluss.append(time.time()-start_time)
            regimes= list(filter(lambda x: x != 0, x["regimes"]))
            regimes= list(filter(lambda x: x != len(df), regimes))
        except Exception as e:
            regimes=[]
            pass 
        all_regimes.append(regimes)
        pbar.update(1)
    print(time.time()-start_all)
    print(sum(timings_mp), "MP computation time")
    print(sum(timings_fluss), "semantic seg time")
    df_regimes=pd.DataFrame(all_regimes)
    return df_regimes

def getHistogramFromUnalignedDf(df_regimes:pd.DataFrame(), ts, ts_min,ts_max):
    import math
    all_ts=list(range(ts_min, ts_max+1000,1000))
    histogram = [0] * len(all_ts)
    try:
        for index, rows in df_regimes.iterrows(): 
            for r in rows:
                if(math.isnan(r)==False):
                    r=int(r)
                    local_ts=ts[index][r]
                    global_ind=all_ts.index(local_ts)
                    histogram[global_ind]=histogram[global_ind]+1
    except Exception as e:
        print(e)
        return 
    return histogram

    
if __name__ == "__main__":
    from datetime import datetime
    import statistics
    import matplotlib.pyplot as plt
    from scipy.interpolate import interp1d
    from scipy import interpolate

    import numpy as np
    c=get_ssh_connection()
    if(c is not None):
        from_date=datetime(2020,7, 17, 10, 0, 0)
        to_date=datetime(2020,7, 17, 10, 59, 59)
        from_date = int(time.mktime(from_date.timetuple())*1000)
        to_date = int(time.mktime(to_date.timetuple())*1000)
        all_data=get_data_from_mrF(from_date=from_date,to_date=to_date)
    c.close()
    #get regime changes
    df_regimes_price=get_regime_changes(all_data["df_price_data"],num_regimes=5,windows=[2])
    df_regimes_volume=get_regime_changes(all_data["df_volume_data"],num_regimes=5,windows=[2])
    
    #Histograms
    histogram_price=getHistogramFromUnalignedDf(df_regimes_price,all_data["ts_price"],all_data["ts_price_min"],all_data["ts_price_max"])
    histogram_volume=getHistogramFromUnalignedDf(df_regimes_volume,all_data["ts_volume"],all_data["ts_volume_min"],all_data["ts_volume_max"])
    
    #events price
    all_ts=list(range(all_data["ts_price_min"], all_data["ts_price_max"]+1000,1000))
    date_time_stamps=[datetime.fromtimestamp(i/1000) for i in all_ts]

    plt.stem(date_time_stamps,histogram_price,markerfmt=" ")
    plt.stem(date_time_stamps,histogram_volume,markerfmt=" ")
    #Events
    events_price=TimeSeriesEvents.getCandidateEvents(histogram_price,len(all_ts),ts_freq_threshold=12,peek_ratio=0.3,sampling_rate=1)
    #TimeSeriesL1Analytics.plotEventHistograms(histogram_price,len(all_ts),events_price)
    number_of_samples=len(all_ts)
    plt.bar(range(number_of_samples),histogram_volume,color='C0',width=3)
    for i,row in events_price.iterrows():
        start_event=row[0]
        end_event=row[2]
        peek=row[1]
        x=[start_event,peek,end_event]
        y=[0,histogram_price[peek],0]
        print(x,y)
        x2 = np.linspace(x[0], x[-1], 1000)
        y2 = interpolate.pchip_interpolate(x, y, x2)
        plt.plot(x2, y2)
    plt.show()
    #events volume
    all_ts=list(range(all_data["ts_volume_min"], all_data["ts_volume_max"]+1000,1000))
    date_time_stamps=[datetime.fromtimestamp(i/1000) for i in all_ts]
    number_of_samples=len(all_ts)
    events_volume=TimeSeriesEvents.getCandidateEvents(histogram_volume,len(all_ts),ts_freq_threshold=12,peek_ratio=0.3,sampling_rate=1)
    plt.bar(range(number_of_samples),histogram_volume,color='C0',width=3) 
    for i,row in events_volume.iterrows():
        start_event=row[0]
        end_event=row[2]
        peek=row[1]
        x=[start_event,peek,end_event]
        y=[0,histogram_volume[peek],0]
        x2 = np.linspace(x[0], x[-1], 100)
        print(x,y)
        y2 = interpolate.pchip_interpolate(x, y, x2)
        plt.plot(x2, y2)
    plt.show()
    #indicators
    li=[]
    mi=[]
    ti=[]
    all_ts=list(range(all_data["ts_price_min"], all_data["ts_price_max"]+1000,1000))
    for i,r in events_price.iterrows():
        l=all_ts[r["leading indicator"]]
        m=all_ts[r["main indicator"]]
        t=all_ts[r["trailing indicator"]]
        tmp_l=[]
        tmp_m=[]
        tmp_t=[]
        ts=all_data["ts_price"]
        tickers=list(all_data["df_price_data"].columns)
        for j,regime_changes in df_regimes_price.iterrows():
            for rc in regime_changes :
                if(str(rc)!='nan'):
                    rc=int(rc)
                    local_ts=ts[j][rc]                    
                    if(l == local_ts): tmp_l.append(tickers[j])
                    if(m == local_ts): tmp_m.append(tickers[j])
                    if(t == local_ts): tmp_t.append(tickers[j])
        li.append(tmp_l)
        mi.append(tmp_m)
        ti.append(tmp_t)
    indicators_price=pd.DataFrame({"li":li,"mi":mi,"ti":ti})
    
    li=[]
    mi=[]
    ti=[]
    all_ts=list(range(all_data["ts_volume_min"], all_data["ts_volume_max"]+1000,1000))
    for i,r in events_volume.iterrows():
        l=all_ts[r["leading indicator"]]
        m=all_ts[r["main indicator"]]
        t=all_ts[r["trailing indicator"]]
        tmp_l=[]
        tmp_m=[]
        tmp_t=[]
        ts=all_data["ts_volume"]
        tickers=list(all_data["df_volume_data"].columns)
        for j,regime_changes in df_regimes_volume.iterrows():
            for rc in regime_changes :
                if(str(rc)!='nan'):
                    rc=int(rc)
                    local_ts=ts[j][rc]                    
                    if(l == local_ts): tmp_l.append(tickers[j])
                    if(m == local_ts): tmp_m.append(tickers[j])
                    if(t == local_ts): tmp_t.append(tickers[j])
        li.append(tmp_l)
        mi.append(tmp_m)
        ti.append(tmp_t)
    indicators_volume=pd.DataFrame({"li":li,"mi":mi,"ti":ti})
    

    merged_hist=[sum(x) for x in zip(histogram_price, histogram_volume)]
    merged_events=TimeSeriesEvents.getCandidateEvents(merged_hist,len(all_ts),ts_freq_threshold=18,peek_ratio=0.3,sampling_rate=1)
    plt.bar(range(number_of_samples),merged_hist,color='C0',width=3) 
    for i,row in merged_events.iterrows():
        start_event=row[0]
        end_event=row[2]
        peek=row[1]
        x=[start_event,peek,end_event]
        y=[0,merged_hist[peek],0]
        x2 = np.linspace(x[0], x[-1], 100)
        print(x,y)
        y2 = interpolate.pchip_interpolate(x, y, x2)
        plt.plot(x2, y2)
    plt.show()
    #MARKET CAPITAL ESTIMATION
    market_li=[]
    market_mi=[]
    market_ti=[]
    for i,r in indicators_price.iterrows():
        li_list=r["li"]
        mi_list=r["mi"]
        ti_list=r["ti"]
        li_ts=all_ts[events_price.iloc[i,0]]
        mi_ts=all_ts[events_price.iloc[i,1]]
        ti_ts=[events_price.iloc[i,2]]
        tmp_li_mc=0
        for tckr in li_list:
            col_index=list(all_data["df_price_data"].columns).index(tckr)
            ts_non_align_index=all_data["ts_price"][col_index].index(li_ts)
            tmp_li_mc=tmp_li_mc+   np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]) 
        market_li.append(tmp_li_mc)
        
        tmp_mi_mc=0
        for tckr in mi_list:
            col_index=list(all_data["df_price_data"].columns).index(tckr)
            ts_non_align_index=all_data["ts_price"][col_index].index(mi_ts)
            tmp_mi_mc=tmp_mi_mc+   np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]) 
        market_mi.append(tmp_mi_mc)
        
        tmp_ti_mc=0
        for tckr in ti_list:
            col_index=list(all_data["df_price_data"].columns).index(tckr)
            if(ti_ts in all_data["ts_price"][col_index]):
                ts_non_align_index=all_data["ts_price"][col_index].index(ti_ts)
            else: 
                ts_non_align_index=len(all_data["ts_price"][col_index])-1
            tmp_ti_mc=tmp_ti_mc+   np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]) 
        market_ti.append(tmp_ti_mc)
    market_capital_price=pd.DataFrame({"market_li":market_li,"market_mi":market_mi,"market_ti":market_ti})

    #SECTORS
    import networkx as nx
    G=nx.read_graphml("finL2Extension.graphml")
    li_industries=[]
    li_sectors=[]
    mi_industries=[]
    mi_sectors=[]
    ti_industries=[]
    ti_sectors=[]
    for i,r in indicators_price.iterrows():
        tmp_li_ind=[]
        tmp_li_sect=[]
        for t in r["li"]: 
            subg=nx.ego_graph(G,t,1).nodes(data=True)
            for n in subg:
                if(len(n)>1):
                    if('industry' in n[1].keys()):
                         tmp_li_ind.append(n[1]["industry"])
                    if('sector' in n[1].keys()):
                         tmp_li_sect.append(n[1]["sector"])
        tmp_li_ind=list(dict.fromkeys(tmp_li_ind))
        tmp_li_sect=list(dict.fromkeys(tmp_li_sect))
        
        tmp_mi_ind=[]
        tmp_mi_sect=[]
        for t in r["mi"]: 
            subg=nx.ego_graph(G,t,1).nodes(data=True)
            for n in subg:
                if(len(n)>1):
                    if('industry' in n[1].keys()):
                         tmp_mi_ind.append(n[1]["industry"])
                    if('sector' in n[1].keys()):
                         tmp_mi_sect.append(n[1]["sector"])
        tmp_mi_ind=list(dict.fromkeys(tmp_mi_ind))
        tmp_mi_sect=list(dict.fromkeys(tmp_mi_sect))
        
        tmp_ti_ind=[]
        tmp_ti_sect=[]
        for t in r["ti"]: 
            subg=nx.ego_graph(G,t,1).nodes(data=True)
            for n in subg:
                if(len(n)>1):
                    if('industry' in n[1].keys()):
                         tmp_ti_ind.append(n[1]["industry"])
                    if('sector' in n[1].keys()):
                         tmp_ti_sect.append(n[1]["sector"])
        tmp_ti_ind=list(dict.fromkeys(tmp_ti_ind))
        tmp_ti_sect=list(dict.fromkeys(tmp_ti_sect))
        li_industries.append(tmp_li_ind)
        li_sectors.append(tmp_li_sect)
        mi_industries.append(tmp_mi_ind)
        mi_sectors.append(tmp_mi_sect)
        ti_industries.append(tmp_ti_ind)
        ti_sectors.append(tmp_mi_sect)
    
    df_sectors=pd.DataFrame({"li_sectors":li_sectors,"mi_sectors":mi_sectors,"ti_sectors":ti_sectors})
    df_industries=pd.DataFrame({"li_industries":li_industries,"mi_industries":mi_industries,"ti_industries":ti_industries})
    
    #from itertools import chain
    #all_data={"ts_price":ts_price,"df_price_data":df_price_data,"ts_price_min":ts_price_min,"ts_volume":ts_volume,"df_volume_data":df_volume_data,"ts_volume_min":ts_volume_min}
    #start_all=time.time()
    #all_data=get_ts_from_finny()
    #print(time.time()-start_all, "seconds to retrive data size of",len(all_data))
    #1875.3096759319305 seconds to retrive data size of 3948
    #start_all=time.time()
    #df_price_time, df_volume_time,df_price_data,df_volume_data=construct_df_from_ts(all_data)
    #print(time.time()-start_all, "seconds to split data into df's")
    #import pickle
    #with open('1h_all_data.pkl', 'wb') as f:
    #    pickle.dump(all_data, f)
    
    #import pickle
    #with open('all_data.pkl', 'rb') as f:
    #    all_data = pickle.load(f)
    #for d in all_data:
        #if("CSCO" in d["key"] and "price" in d["key"]):break
    # ts,data = map(list,zip(*d["data"]))
    # profile=mp.compute(data,windows=[10])
    # profile = mp.discover.motifs(profile, k=1)
    # x=mp.discover.regimes(profile, num_regimes=50)
    # profile, figures = mp.analyze(data)
    # figures = mp.visualize(profile)
    # daily_profile = mp.discover.discords(profile)
    # figures = mp.visualize(daily_profile)

    # from datetime import datetime
    # print(datetime.fromtimestamp(ts[0]/1000))
    # print(datetime.fromtimestamp(ts[-1]/1000))
    
    # print(datetime.fromtimestamp(ts[profile["discords"][0]]/1000))
    # print(datetime.fromtimestamp(ts[profile["discords"][1]]/1000))
    # print(datetime.fromtimestamp(ts[profile["discords"][2]]/1000))
    # #b69b21b7f71749d5965c07aa8d695ecb
    # from newsapi import NewsApiClient
    # newsapi = NewsApiClient(api_key='b69b21b7f71749d5965c07aa8d695ecb')
    # all_articles = newsapi.get_everything(
    # q='Cisco',
    # language='en',  
    # from_param='2020-07-16',
    # to='2020-07-17',
    # )
    # for article in all_articles['articles']:
    #     print('Source : ',article['source']['name'])
    #     print('Title : ',article['title'])
    #     print('Description : ',article['description'],'\n\n')
    # plt.plot(data)

