import time
import pandas as pd
import matplotlib.pyplot as plt
import matrixprofile as mp
import numpy as np
import redis
from redistimeseries.client import Client
from scipy import interpolate
_=np.seterr(all="ignore")
from datetime import datetime,date,timedelta
import time
def get_data_from_mrF(redis_host="localhost",redis_port=6379,from_time=0,to_time=-1,
                     query_key=None,prefix='rts1:01:',aggregation_type="last",bucket_size_msec=60000, last_batch_control_variable="mac_simlooping", filters="SYMSET=ACTIVE"):
    all_data={}
    r = redis.Redis(host=redis_host,port=redis_port)
    #if this is the last batch return empty
    if(r.exists(last_batch_control_variable)):
        print("Not processing the end-of-day batch")
        return all_data
    rts = Client(host=redis_host, port=redis_port)
    ts_price=[]
    ts_volume=[]
    data_price=[]
    data_volume=[]
    keys_price=[]
    keys_volume=[]
    ts_price_min=[]
    ts_volume_min=[]
    ts_price_max=[]
    ts_volume_max=[]
    from_time=int(from_time)
    to_time=int(to_time)
    filters=filters.split(",")
    try:
        if(query_key==None):
            #all_keys=r.execute_command("keys *")
            print("Querying data...")
            start=time.time()
            bulk_data=[]
            for f in filters:
                bulk_data.extend(rts.mrange(from_time=from_time,to_time=to_time,aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=[f]))
            print("Querying completed:",int(time.time()-start),"sec.")
            print("Splitting data into price and volume...")
            for d in bulk_data:
                key=str(list(d.keys())[0]) #name of time series
                rest=list(d.get(key))[1]
                ts,data = map(list,zip(*rest)) # timestamps and data
                if(prefix in key and "price" in key):
                    ts_price_min.extend(ts) 
                    ts_price_min=[min(ts_price_min)]
                    ts_price_max.extend(ts)
                    ts_price_max=[max(ts_price_max)]
                    ts_price.append(ts)
                    data_price.append(data)
                    keys_price.append(key.split(":")[3]) 
                elif(prefix in key and "volume" in key):
                    ts_volume_min.extend(ts) 
                    ts_volume_min=[min(ts_volume_min)]
                    ts_volume_max.extend(ts)
                    ts_volume_max=[max(ts_volume_max)]
                    ts_volume.append(ts)
                    data_volume.append(data)
                    keys_volume.append(key.split(":")[3])
    except Exception as e:
        print(e)
    print("Splitting completed.")
    df_price_data=pd.DataFrame(data_price)
    df_price_data=df_price_data.transpose()
    df_price_data.columns=keys_price
    df_volume_data=pd.DataFrame(data_volume)
    df_volume_data=df_volume_data.transpose()
    df_volume_data.columns=keys_volume
    if(len(ts_price_min)>0 and len(ts_price_max)>0 and len(ts_volume_min)>0 and len(ts_volume_max)>0):
        all_data={"ts_price":ts_price,"df_price_data":df_price_data,"ts_price_min":ts_price_min[0],"ts_price_max":ts_price_max[0],"ts_volume":ts_volume,"df_volume_data":df_volume_data,"ts_volume_min":ts_volume_min[0],"ts_volume_max":ts_volume_max[0]}
    return all_data

def get_regime_changes(df,num_regimes=50,windows=[10]):
    #from tqdm import tqdm
    #Matrix profile
    timings_mp=[]    
    timings_fluss=[]
    all_regimes=[]
    start_all=time.time()
    #pbar=tqdm(total=len(df.columns),position=0)
    for i in range(len(df.columns)):
        ts=list(df.iloc[:,i])
        ts=[x for x in ts if str(x)!='nan']
        try:
            start_time = time.time()
            profile=mp.compute(ts,windows=windows)
            timings_mp.append(time.time()-start_time)
            start_time = time.time()
            x=mp.discover.regimes(profile, num_regimes=num_regimes)
            timings_fluss.append(time.time()-start_time)
            regimes= list(filter(lambda x: x != 0, x["regimes"]))
            regimes= list(filter(lambda x: x != len(df), regimes))
        except Exception as e:
            regimes=[]
            #print(e)
            #print("Try lowering the window size for matrix profile")
            pass 
        all_regimes.append(regimes)
        #pbar.update(1)
    print(time.time()-start_all, "sec of total time....",sum(timings_mp), " for MP computation,",sum(timings_fluss), "for semantic seg")
    df_regimes=pd.DataFrame(all_regimes)
    return df_regimes

def getHistogramFromUnalignedDf(df_regimes:pd.DataFrame(), ts, ts_min,ts_max,bucket_size_msec,window_size=None):
    import math
    all_ts=list(range(ts_min, ts_max+bucket_size_msec,bucket_size_msec))
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
    #if(window_size is not None):histogram[window_size]=1
    return histogram

def plotMSigEvents(number_of_samples,histogram,events,title,bucket_size_msec):
    plt.stem(range(number_of_samples),histogram,markerfmt=" ")
    plt.title(title)
    for i,row in events.iterrows():
        start_event=row[0]
        end_event=row[2]
        peek=row[1]
        x=[start_event,peek,end_event]
        y=[0,histogram[peek],0]
        print(x,y)
        x2 = np.linspace(x[0], x[-1], bucket_size_msec)
        y2 = interpolate.pchip_interpolate(x, y, x2)
        plt.plot(x2, y2)
    return plt
def getIndicators(all_data,events,df_regimes,ts_min,ts_max,ts_name,df_type_data_name,bucket_size_msec):
        #indicators
    li=[]
    mi=[]
    ti=[]
    all_ts=list(range(ts_min, ts_max+bucket_size_msec,bucket_size_msec))
    for i,r in events.iterrows():
        l=all_ts[r["leading indicator"]]
        m=all_ts[r["main indicator"]]
        t=all_ts[r["trailing indicator"]]
        tmp_l=[]
        tmp_m=[]
        tmp_t=[]
        ts=all_data[ts_name]
        tickers=list(all_data[df_type_data_name].columns)
        for j,regime_changes in df_regimes.iterrows():
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
    indicators=pd.DataFrame({"li":li,"mi":mi,"ti":ti})
    return indicators

def getMarketCapitalPerEvent(all_ts,all_data,events_price,indicators_price):
        #MARKET CAPITAL ESTIMATION
    market_dict=[]
    for i,r in indicators_price.iterrows():
        li_list=r["li"]
        mi_list=r["mi"]
        ti_list=r["ti"]
        li_ts=all_ts[events_price.iloc[i,0]]
        mi_ts=all_ts[events_price.iloc[i,1]]
        ti_ts=all_ts[events_price.iloc[i,2]]
        for tckr in li_list: #market capital for leading indicators
            col_index=list(all_data["df_price_data"].columns).index(tckr)
            if(li_ts in all_data["ts_price"][col_index]):
                ts_non_align_index=all_data["ts_price"][col_index].index(li_ts) 
            else: 
                ts_non_align_index=len(all_data["ts_price"][col_index])-1  
            market_dict.append({"event_number":i+1,"symbol":tckr, "price": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]),
                                "volume":np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),
                                "market_capital": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"indicator_type":"leading indicator"})
        for tckr in mi_list: #market capital for main indicators
            col_index=list(all_data["df_price_data"].columns).index(tckr)
            if(mi_ts in all_data["ts_price"][col_index]):
                ts_non_align_index=all_data["ts_price"][col_index].index(mi_ts)
            else: 
                ts_non_align_index=len(all_data["ts_price"][col_index])-1    
            market_dict.append({"event_number":i+1,"symbol":tckr, "price": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]),"market_capital": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"volume":np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"indicator_type":"main indicator"})
        for tckr in ti_list:#market capital for trailing indicators
            col_index=list(all_data["df_price_data"].columns).index(tckr)
            if(ti_ts in all_data["ts_price"][col_index]):
                ts_non_align_index=all_data["ts_price"][col_index].index(ti_ts)
            else: 
                ts_non_align_index=len(all_data["ts_price"][col_index])-1
            market_dict.append({"event_number":i+1,"symbol":tckr, "price": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]),"market_capital": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"volume":np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"indicator_type":"trailing indicator"})
       
    df_market_capital_price=pd.DataFrame(market_dict)
    return df_market_capital_price
# def getMarketCapitalPerEvent(all_ts,all_data,events_price,indicators_price,category='gain',enableMP=True,window_size=10):
#     #MARKET CAPITAL ESTIMATION
#     if(enableMP):
#         market_dict=[]
#         for i,r in indicators_price.iterrows():
#             li_list=r["li"]
#             mi_list=r["mi"]
#             ti_list=r["ti"]
#             li_ts=all_ts[events_price.iloc[i,0]]
#             mi_ts=all_ts[events_price.iloc[i,1]]
#             ti_ts=[events_price.iloc[i,2]]
#             for tckr in li_list: #market capital for leading indicators
#                 col_index=list(all_data["df_price_data"].columns).index(tckr)
#                 ts_non_align_index=all_data["ts_price"][col_index].index(li_ts)            
#                 market_dict.append({"event_number":i+1,"symbol":tckr, "price": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]),"volume":np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"market_capital": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"indicator_type":"leading indicator"})
#             for tckr in mi_list: #market capital for main indicators
#                 col_index=list(all_data["df_price_data"].columns).index(tckr)
#                 ts_non_align_index=all_data["ts_price"][col_index].index(mi_ts)
#                 market_dict.append({"event_number":i+1,"symbol":tckr, "price": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]),"market_capital": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"volume":np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"indicator_type":"main indicator"})
#             for tckr in ti_list:#market capital for trailing indicators
#                 col_index=list(all_data["df_price_data"].columns).index(tckr)
#                 if(ti_ts in all_data["ts_price"][col_index]):
#                     ts_non_align_index=all_data["ts_price"][col_index].index(ti_ts)
#                 else: 
#                     ts_non_align_index=len(all_data["ts_price"][col_index])-1
#                 market_dict.append({"event_number":i+1,"symbol":tckr, "price": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]),"market_capital": np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index]) * np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"volume":np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index]),"indicator_type":"trailing indicator"})
           
#         df_market_capital_price=pd.DataFrame(market_dict)
#         return df_market_capital_price
    # else:
    #     #events_price=events_price_gain
    #     #indicators_price=indicators_price_gain
    #     market_dict=[]
    #     for i,r in indicators_price.iterrows():
    #         li_list=r["li"]
    #         mi_list=r["mi"]
    #         ti_list=r["ti"]
    #         li_ts=events_price.iloc[i,0]
    #         mi_ts=events_price.iloc[i,1]
    #         ti_ts=events_price.iloc[i,2]
    #         for tckr in li_list: #market capital for leading indicators
    #             col_index=list(all_data["df_price_data"].columns).index(tckr)
    #             ts_non_align_index=li_ts
    #             event_number=i+1
    #             symbol=tckr
    #             price=np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index])
    #             volume=np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index])
    #             price_before=np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index-window_size+1])
    #             volume_before=np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index-window_size+1])
    #             market_capital=(price*volume)-(price_before*volume_before)
    #             indicator_type="leading indicator"
    #             market_dict.append({"event_number":event_number,"symbol":symbol, "price": price,"volume":volume,"market_capital": market_capital,"indicator_type":indicator_type})
            
        
    #         for tckr in mi_list: #market capital for main indicators
    #             col_index=list(all_data["df_price_data"].columns).index(tckr)
    #             ts_non_align_index=mi_ts
    #             event_number=i+1
    #             symbol=tckr
    #             price=np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index])
    #             volume=np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index])
    #             price_before=np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index-window_size+1])
    #             volume_before=np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index-window_size+1])
    #             market_capital=(price*volume)-(price_before*volume_before)
    #             indicator_type="main indicator"
    #             market_dict.append({"event_number":event_number,"symbol":symbol, "price": price,"volume":volume,"market_capital": market_capital,"indicator_type":indicator_type})
            
    #         for tckr in ti_list: #market capital for trailing indicators
    #             col_index=list(all_data["df_price_data"].columns).index(tckr)
    #             ts_non_align_index=ti_ts
    #             event_number=i+1
    #             symbol=tckr
    #             price=np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index])
    #             volume=np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index])
    #             price_before=np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index-window_size+1])
    #             volume_before=np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index-window_size+1])
    #             market_capital=(price*volume)-(price_before*volume_before)
    #             indicator_type="trailing indicator"
    #             market_dict.append({"event_number":event_number,"symbol":symbol, "price": price,"volume":volume,"market_capital": market_capital,"indicator_type":indicator_type})
        
    #     df_market_capital_price=pd.DataFrame(market_dict)
    #     return df_market_capital_price
    
def getSectorIndustryPerEvent(indicators_price,L2name):
    #SECTORS
    import networkx as nx
    G=nx.read_graphml(L2name)
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
            if(t in list(G.nodes())):
                subg=nx.ego_graph(G,t,1).nodes(data=True)
                for n in subg:
                    if(len(n)>1):
                        if('industry' in n[1].keys()):
                              tmp_li_ind.append(n[1]["industry"])
                        if('sector' in n[1].keys()):
                              tmp_li_sect.append(n[1]["sector"])
            else:
                print("unable to find the symbol:",t, "in",L2name," Update the KG...")
        tmp_li_ind=list(dict.fromkeys(tmp_li_ind))
        tmp_li_sect=list(dict.fromkeys(tmp_li_sect))
        
        tmp_mi_ind=[]
        tmp_mi_sect=[]
        for t in r["mi"]: 
            if(t in list(G.nodes())):
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
            if(t in list(G.nodes())):
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
        ti_sectors.append(tmp_ti_sect)
    
    df_sectors=pd.DataFrame({"li_sectors":li_sectors,"mi_sectors":mi_sectors,"ti_sectors":ti_sectors})
    df_industries=pd.DataFrame({"li_industries":li_industries,"mi_industries":mi_industries,"ti_industries":ti_industries})
    return df_sectors,df_industries

def getIDsFromMySQL(cursor):
    try: 
        result=cursor.execute("SELECT MAX(event_id) FROM events")
        result=cursor.fetchone()
        if(list(result)[0]==None):
            print("event table looks empty...")
            event_id=1
            li_group_id=1
            mi_group_id=1
            ti_group_id=1
            sector_group_id=1
            industry_group_id=1 
        else:
            #Assumption no event can be added without li, mi, ti
            ti_group_id=mi_group_id=li_group_id=event_id=list(result)[0]+1
            #Assumption: sector and industry can be empty in previous insertions
            result=cursor.execute("SELECT MAX(sector_group_id) FROM sector_groups")
            result=cursor.fetchone()
            sector_group_id=list(result)[0]
            if(sector_group_id is not None):sector_group_id=sector_group_id+1
            result=cursor.execute("SELECT MAX(industry_group_id) FROM industry_groups")
            result=cursor.fetchone()
            industry_group_id=list(result)[0]
            if(industry_group_id is not None):industry_group_id=industry_group_id+1
    except Exception as e:
        print(e)
        return
    return event_id,li_group_id, mi_group_id, ti_group_id,sector_group_id,industry_group_id 

def sendToMysql(msig_data,mysql_host,mysql_port,mysql_db,mysql_user,mysql_pass):
    import mysql.connector
    event_price_ids=[]
    event_volume_ids=[]
    
    try:
        cnx = mysql.connector.connect(host=mysql_host,
                                   port=mysql_port,
                                   user=mysql_user,
                                   password=mysql_pass,
                                   database=mysql_db
                                   )
    except Exception as e:
        print(e)
        return
    cursor=cnx.cursor(buffered=True)
    #INSERT PRICE EVENTS!!!!
    for i,e in msig_data["events_price"].iterrows():
        event_id,li_group_id, mi_group_id, ti_group_id,sector_group_id,industry_group_id=getIDsFromMySQL(cursor)
        event_price_ids.append(event_id)
        print("inserting price event number:",i+1)
        market_capitals_all_events=msig_data["df_market_capital_price"].groupby('event_number',as_index=False).sum()
        if(i+1 not in market_capitals_all_events["event_number"].values):continue
        market_capital=float(market_capitals_all_events[market_capitals_all_events["event_number"]==i+1]["market_capital"].values)
        category="price"
        loop_num=msig_data["loop_num"]
        batch_min=min(map(lambda x: x[-1],msig_data["ts_price"]))
        batch_max=max(map(lambda x: x[-1],msig_data["ts_price"]))
        batch_bucket_size=msig_data["ts_price"][0][1]-msig_data["ts_price"][0][0]
        li_time=e["leading indicator"]
        mi_time=e["main indicator"]
        ti_time=e["trailing indicator"]
        is_predicted=0
        #create event
        sql="INSERT INTO events (event_id, li_group_id, mi_group_id,ti_group_id,sector_group_id,industry_group_id,market_capital,category,\
        loop_num,batch_min, batch_max,batch_bucket_size,li_time,mi_time,ti_time,is_predicted) \
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        sql_data=(event_id,li_group_id,mi_group_id,ti_group_id,sector_group_id,industry_group_id,market_capital,category,loop_num,\
                  batch_min, batch_max,batch_bucket_size,li_time,mi_time,ti_time,is_predicted)
        resp=cursor.execute(sql,sql_data)
        cnx.commit()
        #create li mi ti groups
        indicator_market_capital=msig_data["df_market_capital_price"].groupby(['event_number','indicator_type'],as_index=False).sum()
        indicator_market_capital=indicator_market_capital[indicator_market_capital["event_number"]==i+1]
        if(len(indicator_market_capital[indicator_market_capital["indicator_type"]=="leading indicator"].values)==0):
            li_group_market_capital=0
        else:
            li_group_market_capital=float(indicator_market_capital[indicator_market_capital["indicator_type"]=="leading indicator"]["market_capital"].values)
        
        if(len(indicator_market_capital[indicator_market_capital["indicator_type"]=="main indicator"].values)==0):
            mi_group_market_capital=0
        else:
            mi_group_market_capital=float(indicator_market_capital[indicator_market_capital["indicator_type"]=="main indicator"]["market_capital"].values)
        
        if(len(indicator_market_capital[indicator_market_capital["indicator_type"]=="trailing indicator"].values)==0):
            ti_group_market_capital=0
        else:
            ti_group_market_capital=float(indicator_market_capital[indicator_market_capital["indicator_type"]=="trailing indicator"]["market_capital"].values)
    
        sql="INSERT INTO li_groups (event_id,li_group_id,li_group_market_capital) VALUES(%s,%s,%s)"
        sql_data=(event_id,li_group_id,li_group_market_capital)
        resp=cursor.execute(sql,sql_data)
        sql="INSERT INTO mi_groups (event_id,mi_group_id,mi_group_market_capital) VALUES(%s,%s,%s)"
        sql_data=(event_id,mi_group_id,mi_group_market_capital)
        resp=cursor.execute(sql,sql_data)
        sql="INSERT INTO ti_groups (event_id,ti_group_id,ti_group_market_capital) VALUES(%s,%s,%s)"
        sql_data=(event_id,ti_group_id,ti_group_market_capital)
        resp=cursor.execute(sql,sql_data)
        cnx.commit()
        #create sector and industry groups
        sql="INSERT INTO sector_groups (event_id,sector_group_id) VALUES(%s,%s)"
        sql_data=(event_id,sector_group_id)
        resp=cursor.execute(sql,sql_data)
        sql="INSERT INTO industry_groups (event_id,industry_group_id) VALUES(%s,%s)"
        sql_data=(event_id,industry_group_id)
        resp=cursor.execute(sql,sql_data)    
        cnx.commit()
        #insert indicators to the tables. USING EXECUTEMANY HERE
        sql_li="INSERT INTO leading_indicators (li_group_id,symbol,li_market_capital) VALUES(%s,%s,%s)"
        sql_data_li=[]
        sql_mi="INSERT INTO main_indicators (mi_group_id,symbol,mi_market_capital) VALUES(%s,%s,%s)"
        sql_data_mi=[]
        sql_ti="INSERT INTO trailing_indicators (ti_group_id,symbol,ti_market_capital) VALUES(%s,%s,%s)"
        sql_data_ti=[]
        for k,row in msig_data["df_market_capital_price"].iterrows():
            event_number=row["event_number"]    
            if(event_number==i+1):
                symbol=row["symbol"] 
                indicator_mcap=row["market_capital"] 
                indicator_type=row["indicator_type"]
                if(indicator_type=="leading indicator"):
                    sql_data_li.append((li_group_id,symbol,indicator_mcap))
                elif(indicator_type=="main indicator"):
                    sql_data_mi.append((mi_group_id,symbol,indicator_mcap))
                else:
                    sql_data_ti.append((ti_group_id,symbol,indicator_mcap))                    
        if(len(sql_data_li)>0):resp=cursor.executemany(sql_li,sql_data_li)
        if(len(sql_data_mi)>0):resp=cursor.executemany(sql_mi,sql_data_mi)
        if(len(sql_data_ti)>0):resp=cursor.executemany(sql_ti,sql_data_ti)
        cnx.commit()
        #insert industries
        sql_industries="INSERT INTO industries(industry_group_id,industry,indicator_type) VALUES(%s,%s,%s)"
        sql_data_industry=[]
        for k,row in msig_data["df_industries_price"].iterrows():
            if(k==i):
                li_industries=row["li_industries"]
                mi_industries=row["mi_industries"]
                ti_industries=row["ti_industries"]
                for li in li_industries:
                    sql_data_industry.append((industry_group_id,li,"leading"))
                for mi in mi_industries:
                    sql_data_industry.append((industry_group_id,mi,"main"))
                for ti in ti_industries:
                    sql_data_industry.append((industry_group_id,ti,"trailing"))
        if(len(sql_data_industry)>0):resp=cursor.executemany(sql_industries,sql_data_industry)
        cnx.commit()
        #insert sectors
        sql_sectors="INSERT INTO sectors (sector_group_id,sector,indicator_type) VALUES(%s,%s,%s)"
        sql_data_sector=[]
        for k,row in msig_data["df_sectors_price"].iterrows():
            if(k==i):
                li_sectors=row["li_sectors"]
                mi_sectors=row["mi_sectors"]
                ti_sectors=row["ti_sectors"]
                for li in li_sectors:
                    sql_data_sector.append((sector_group_id,li,"leading"))
                for mi in mi_sectors:
                    sql_data_sector.append((sector_group_id,mi,"main"))
                for ti in ti_sectors:
                    sql_data_sector.append((sector_group_id,ti,"trailing"))
        if(len(sql_data_sector)>0):resp=cursor.executemany(sql_sectors,sql_data_sector)
        cnx.commit()
    #### INSERT VOLUME EVENTS
    for i,e in msig_data["events_volume"].iterrows():
        event_id,li_group_id, mi_group_id, ti_group_id,sector_group_id,industry_group_id=getIDsFromMySQL(cursor)
        event_volume_ids.append(event_id)
        print("inserting volume event number:",i+1)
        market_capitals_all_events=msig_data["df_market_capital_volume"].groupby('event_number',as_index=False).sum()
        if(i+1 not in market_capitals_all_events["event_number"].values):continue
        market_capital=float(market_capitals_all_events[market_capitals_all_events["event_number"]==i+1]["market_capital"].values)
        category="volume"
        loop_num=msig_data["loop_num"]
        batch_min=min(map(lambda x: x[-1],msig_data["ts_volume"]))
        batch_max=max(map(lambda x: x[-1],msig_data["ts_volume"]))
        batch_bucket_size=msig_data["ts_volume"][0][1]-msig_data["ts_volume"][0][0]
        li_time=e["leading indicator"]
        mi_time=e["main indicator"]
        ti_time=e["trailing indicator"]
        is_predicted=0
        #create event
        sql="INSERT INTO events (event_id, li_group_id, mi_group_id,ti_group_id,sector_group_id,industry_group_id,market_capital,category,\
        loop_num,batch_min, batch_max,batch_bucket_size,li_time,mi_time,ti_time,is_predicted) \
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        sql_data=(event_id,li_group_id,mi_group_id,ti_group_id,sector_group_id,industry_group_id,market_capital,category,loop_num,\
                  batch_min, batch_max,batch_bucket_size,li_time,mi_time,ti_time,is_predicted)
        resp=cursor.execute(sql,sql_data)
        cnx.commit()
        #create li mi ti groups
        indicator_market_capital=msig_data["df_market_capital_volume"].groupby(['event_number','indicator_type'],as_index=False).sum()
        indicator_market_capital=indicator_market_capital[indicator_market_capital["event_number"]==i+1]
        if(len(indicator_market_capital[indicator_market_capital["indicator_type"]=="leading indicator"].values)==0):
            li_group_market_capital=0
        else:
            li_group_market_capital=float(indicator_market_capital[indicator_market_capital["indicator_type"]=="leading indicator"]["market_capital"].values)
        
        if(len(indicator_market_capital[indicator_market_capital["indicator_type"]=="main indicator"].values)==0):
            mi_group_market_capital=0
        else:
            mi_group_market_capital=float(indicator_market_capital[indicator_market_capital["indicator_type"]=="main indicator"]["market_capital"].values)
        
        if(len(indicator_market_capital[indicator_market_capital["indicator_type"]=="trailing indicator"].values)==0):
            ti_group_market_capital=0
        else:
            ti_group_market_capital=float(indicator_market_capital[indicator_market_capital["indicator_type"]=="trailing indicator"]["market_capital"].values)
    
        sql="INSERT INTO li_groups (event_id,li_group_id,li_group_market_capital) VALUES(%s,%s,%s)"
        sql_data=(event_id,li_group_id,li_group_market_capital)
        resp=cursor.execute(sql,sql_data)
        sql="INSERT INTO mi_groups (event_id,mi_group_id,mi_group_market_capital) VALUES(%s,%s,%s)"
        sql_data=(event_id,mi_group_id,mi_group_market_capital)
        resp=cursor.execute(sql,sql_data)
        sql="INSERT INTO ti_groups (event_id,ti_group_id,ti_group_market_capital) VALUES(%s,%s,%s)"
        sql_data=(event_id,ti_group_id,ti_group_market_capital)
        resp=cursor.execute(sql,sql_data)
        cnx.commit()
        #create sector and industry groups
        sql="INSERT INTO sector_groups (event_id,sector_group_id) VALUES(%s,%s)"
        sql_data=(event_id,sector_group_id)
        resp=cursor.execute(sql,sql_data)
        sql="INSERT INTO industry_groups (event_id,industry_group_id) VALUES(%s,%s)"
        sql_data=(event_id,industry_group_id)
        resp=cursor.execute(sql,sql_data)    
        cnx.commit()
        #insert indicators to the tables. USING EXECUTEMANY HERE
        sql_li="INSERT INTO leading_indicators (li_group_id,symbol,li_market_capital) VALUES(%s,%s,%s)"
        sql_data_li=[]
        sql_mi="INSERT INTO main_indicators (mi_group_id,symbol,mi_market_capital) VALUES(%s,%s,%s)"
        sql_data_mi=[]
        sql_ti="INSERT INTO trailing_indicators (ti_group_id,symbol,ti_market_capital) VALUES(%s,%s,%s)"
        sql_data_ti=[]
        for k,row in msig_data["df_market_capital_volume"].iterrows():
            event_number=row["event_number"]    
            if(event_number==i+1):
                symbol=row["symbol"] 
                indicator_mcap=row["market_capital"] 
                indicator_type=row["indicator_type"]
                if(indicator_type=="leading indicator"):
                    sql_data_li.append((li_group_id,symbol,indicator_mcap))
                elif(indicator_type=="main indicator"):
                    sql_data_mi.append((mi_group_id,symbol,indicator_mcap))
                else:
                    sql_data_ti.append((ti_group_id,symbol,indicator_mcap))                    
        if(len(sql_data_li)>0):resp=cursor.executemany(sql_li,sql_data_li)
        if(len(sql_data_mi)>0):resp=cursor.executemany(sql_mi,sql_data_mi)
        if(len(sql_data_ti)>0):resp=cursor.executemany(sql_ti,sql_data_ti)
        cnx.commit()
        #insert industries
        sql_industries="INSERT INTO industries(industry_group_id,industry,indicator_type) VALUES(%s,%s,%s)"
        sql_data_industry=[]
        for k,row in msig_data["df_industries_volume"].iterrows():
            if(k==i):
                li_industries=row["li_industries"]
                mi_industries=row["mi_industries"]
                ti_industries=row["ti_industries"]
                for li in li_industries:
                    sql_data_industry.append((industry_group_id,li,"leading"))
                for mi in mi_industries:
                    sql_data_industry.append((industry_group_id,mi,"main"))
                for ti in ti_industries:
                    sql_data_industry.append((industry_group_id,ti,"trailing"))
        if(len(sql_data_industry)>0):resp=cursor.executemany(sql_industries,sql_data_industry)
        cnx.commit()
        #insert sectors
        sql_sectors="INSERT INTO sectors (sector_group_id,sector,indicator_type) VALUES(%s,%s,%s)"
        sql_data_sector=[]
        for k,row in msig_data["df_sectors_volume"].iterrows():
            if(k==i):
                li_sectors=row["li_sectors"]
                mi_sectors=row["mi_sectors"]
                ti_sectors=row["ti_sectors"]
                for li in li_sectors:
                    sql_data_sector.append((sector_group_id,li,"leading"))
                for mi in mi_sectors:
                    sql_data_sector.append((sector_group_id,mi,"main"))
                for ti in ti_sectors:
                    sql_data_sector.append((sector_group_id,ti,"trailing"))
        if(len(sql_data_sector)>0):resp=cursor.executemany(sql_sectors,sql_data_sector)
        cnx.commit()
    print("Done")
    cnx.close()
    return event_price_ids,event_volume_ids

def saveSessionInfo(event_price_ids,event_volume_ids,cli_options,start,end_time):
    import mysql.connector

    try:
        cnx = mysql.connector.connect(host=cli_options.mysql_host,
                                   port=cli_options.mysql_port,
                                   user=cli_options.mysql_user,
                                   password=cli_options.mysql_pass,
                                   database=cli_options.mysql_db
                                   )
    except Exception as e:
        print(e)
        return
    cursor=cnx.cursor(buffered=True)
    sql_session="INSERT INTO sessions (start_time,end_time,aggregation_type,bucket_size_msec,enablePlotting,enablePrediction,\
            enableSectorIndustry,filters,from_time,to_time,last_batch_control_variable,msig_host,msig_port,mysql_db,mysql_host,mysql_port, \
            mysql_user,mysql_pass_envar_name,num_regimes,peek_ratio,period,prefix,redis_host,redis_port,ts_freq_threshold,window_size) \
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    if(cli_options.enablePlotting):  
        enablePlotting=1
    else:
        enablePlotting=0
    if(cli_options.enablePrediction):  
        enablePrediction=1
    else:
        enablePrediction=0   
    if(cli_options.enableSectorIndustry):  
        enableSectorIndustry=1
    else:
        enableSectorIndustry=0
    sql_session_data=(int(start),int(end_time),cli_options.aggregation_type,cli_options.bucket_size_msec,enablePlotting,enablePrediction,\
            enableSectorIndustry,str(cli_options.filters),cli_options.from_time,cli_options.to_time,cli_options.last_batch_control_variable,\
            cli_options.msig_host,cli_options.msig_port,cli_options.mysql_db,cli_options.mysql_host,cli_options.mysql_port, \
            cli_options.mysql_user,"MSIG_MYSQL_PASS",cli_options.num_regimes,cli_options.peek_ratio,\
            cli_options.period,cli_options.prefix,cli_options.redis_host,cli_options.redis_port,cli_options.ts_freq_threshold,cli_options.window_size[0])

    _=cursor.execute(sql_session,sql_session_data)
    
    session_id=cursor.lastrowid
    sql_update_price_session_id="UPDATE events SET session_id="+str(session_id)+" WHERE category='price' and event_id in "
    format_strings = ','.join(['%s'] * len(event_price_ids))
    _=cursor.execute(sql_update_price_session_id +"("+ format_strings+")",tuple(event_price_ids))
    
    sql_update_volume_session_id="UPDATE events SET session_id="+str(session_id)+" WHERE category='volume' and event_id in "
    format_strings = ','.join(['%s'] * len(event_volume_ids))
    _=cursor.execute(sql_update_price_session_id +"("+ format_strings+")",tuple(event_volume_ids))

    cnx.commit()

def getDaily2NewsForEvents(df_market_capital_price,indicators_price,todays_start_date_for_news=None,todays_end_date_for_news=None,L2fileName="finL2Extension.graphml"):
    import pandas as pd
    from MNews_Analyzer_start import analyzeNewsUsingRapidAPI
    import networkx as nx
    import time
    from datetime import datetime, timedelta
    print("Checking business-hour news for")
    start=time.time()
    companies=[]
    G=nx.read_graphml(L2fileName)
    all_nodes=pd.DataFrame.from_dict(dict(G.nodes(data=True)),orient='index')
    df_companies_summary=pd.DataFrame(all_nodes[["symbol","fullName"]])

    df_companies_sorted=pd.DataFrame(df_market_capital_price)
    _=df_companies_sorted.sort_values(by=['event_number','market_capital'],ascending=False).groupby('event_number')
    num_events=max(df_companies_sorted['event_number'].values)
    #ADD largest market caps
    for i in range(1,num_events+1):
        df_tmp=df_companies_sorted[df_companies_sorted['event_number']==i].sort_values(by=["market_capital"],ascending=False)
        for j,r in df_tmp.iterrows():
            if(r["symbol"].strip() not in companies):
                companies.append(r["symbol"].strip())
                break
    #ADD top indicators (highest percent change)
    for mi in indicators_price["mi"]:
        for m in mi:
            if(m.strip() not in companies):
               companies.append(m.strip() ) 
               break
    if(len(companies)>0):
        print(companies)
        df_companies_summary=df_companies_summary.loc[df_companies_summary['symbol'].isin(companies)]
        if(todays_start_date_for_news==None):
            x=datetime.today()
            todays_start_date_for_news=(datetime(x.year, x.month, x.day,13,00)-timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')
        if(todays_end_date_for_news==None):
            todays_end_date_for_news=datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
        df_company_daily_news=pd.DataFrame()
        for i,r in df_companies_summary.iterrows():
            q=r["fullName"].strip()
            df_tmp=analyzeNewsUsingRapidAPI(q,r["symbol"].strip(),todays_start_date_for_news,todays_end_date_for_news,page_size=5,category=" ")
        if(len(df_tmp)>0):
           df_company_daily_news=df_company_daily_news.append(df_tmp,ignore_index=True) 
    print("Number of daily news found=",len(df_company_daily_news))
    print("Finished analysing daily news in",time.time()-start,"sec")
    df_company_daily_news["prefix"]="(NEW) "
    return df_company_daily_news

def getDailyCuratedNews(curated_topics):
    import pandas as pd
    df_curated_news=pd.DataFrame()
    from MNews_Analyzer_start import analyzeNewsUsingRapidAPI
    import time
    from datetime import datetime, timedelta
    print("Checking curated news topics...")
    start=time.time()
    x=datetime.today()
    todays_start_date_for_news=(datetime(x.year, x.month, x.day,00,1)).strftime('%Y-%m-%dT%H:%M:%S')
    todays_end_date_for_news=datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
    for topic in curated_topics:
        df_tmp=analyzeNewsUsingRapidAPI(topic,"top news",todays_start_date_for_news,todays_end_date_for_news,page_size=5,category=" ")
        if(len(df_tmp)>0):
             df_curated_news=df_curated_news.append(df_tmp,ignore_index=True)
    print(time.time()-start, "sec. to analyze curated news. Sending them to the front end...")
    return df_curated_news 
        
def generateHtmlStory(msig_data,i,e,event_type,bucket_size_msec=60000,min_ts=int(time.time()*1000),timeZone='US/Pacific',df_company_news=None,category="GAIN",df_company_daily_news=pd.DataFrame()):
    from datetime import datetime
    import pytz
    import pandas as pd
    import numpy as np
    market_cap=0
    start_time="could not be detectected"
    end_time="could not be detected"
    main_time="could not be detected"
    sectors="could not be detected"
    industries="could not be detected"
    companies_table="<br>"
    news_snippet="<br>"
    df_company_news["prefix"]=""
    if(len(df_company_daily_news)>0):
        df_company_news=df_company_news.append(df_company_daily_news,ignore_index=True)
    if(event_type=='price'):
        tmp=list(msig_data["df_sectors_price"].iloc[i,:].values)
        tmp=sum(tmp,[])
        if(len(tmp)>0):
            sectors=', '.join(list(set(tmp)))
            
        tmp=list(msig_data["df_industries_price"].iloc[i,:].values)
        tmp=sum(tmp,[])
        if(len(tmp)>0):
            industries=', '.join(list(set(tmp)))
        
        tmp=msig_data["df_market_capital_price"][msig_data["df_market_capital_price"]["event_number"]==i+1]["market_capital"].values
        if(len(tmp)>0):
            market_cap="$"+str(round(sum(tmp),2))
        
        if(type(e["leading indicator"])==int):
            eventDateTimeStampEpochs= e["leading indicator"] 
            tmp=int((e["leading indicator"]*bucket_size_msec + min_ts))
            tmp=str(datetime.fromtimestamp(tmp/1000).astimezone(pytz.timezone(timeZone)))  
            start_time=tmp[tmp.find(' ')+1:tmp.rfind('-')]
        
        if(type(e["main indicator"])==int):
            eventDateTimeStampEpochs= e["main indicator"] 
            tmp=int((e["main indicator"]*bucket_size_msec + min_ts))
            tmp=str(datetime.fromtimestamp(tmp/1000).astimezone(pytz.timezone(timeZone)))  
            main_time=tmp[tmp.find(' ')+1:tmp.rfind('-')]
        
        if(type(e["trailing indicator"])==int):
            eventDateTimeStampEpochs= e["trailing indicator"] 
            tmp=int((e["trailing indicator"]*bucket_size_msec + min_ts))
            tmp=str(datetime.fromtimestamp(tmp/1000).astimezone(pytz.timezone(timeZone)))  
            end_time=tmp[tmp.find(' ')+1:tmp.rfind('-')]
        
        tmp=pd.DataFrame(msig_data["df_market_capital_price"][msig_data["df_market_capital_price"]["event_number"]==i+1].sort_values(by=["market_capital"],ascending=False))
        tmp=tmp.astype({'volume':'int32'})
        if(len(df_company_news)>0):
            df_event_news=df_company_news[df_company_news["symbol"].isin(list(tmp["symbol"].values))].sort_values(by=["compound"],ascending=False)
            if(category=="GAIN"):
                df_event_news=df_event_news[df_event_news["compound"]>0.05]
                df_event_news["max_compound"]=df_event_news.groupby("symbol")["compound"].transform('max')
                df_event_news=df_event_news[df_event_news["compound"]==df_event_news["max_compound"]].drop(["max_compound"],axis=1)
                df_event_news=df_event_news.drop_duplicates(subset=["newsTitle"],keep="first")
            else:
                df_event_news=df_event_news[df_event_news["compound"]<0]
                df_event_news["min_compound"]=df_event_news.groupby("symbol")["compound"].transform('min')
                df_event_news=df_event_news[df_event_news["compound"]==df_event_news["min_compound"]].drop(["min_compound"],axis=1)
                df_event_news=df_event_news.drop_duplicates(subset=["newsTitle"],keep="last")
            if(len(df_event_news)>0):
               news_snippet="<br> MAGI has found the following news and analyzed them between -1 and 1 related to this event:" 
               for j,n in df_event_news.iterrows():
                   news_snippet=news_snippet+"<li><em>"+str(n["prefix"])+"</em><a href="+str(n["newsLink"])+">"+str(n["newsTitle"])+"</a> (MAGI Score="+str(n["compound"])+").</li>"
                   if(j==50):break
               news_snippet=news_snippet+"<br>" 
        companies_table=tmp.to_html(index=False,header=True,columns=['symbol','price','volume','market_capital','indicator_type'],justify='center',na_rep='Unknown', float_format='%10.2f USD')
        companies_table=companies_table.replace('symbol','Symbol')
        companies_table=companies_table.replace('price','Price')
        companies_table=companies_table.replace('volume','Volume')
        companies_table=companies_table.replace('market_capital','Market Capital')
        companies_table=companies_table.replace('indicator_type','Role')
    else:#volume
        tmp=list(msig_data["df_sectors_volume"].iloc[i,:].values)
        tmp=sum(tmp,[])
        if(len(tmp)>0):
            sectors=', '.join(list(set(tmp)))
            
        tmp=list(msig_data["df_industries_volume"].iloc[i,:].values)
        tmp=sum(tmp,[])
        if(len(tmp)>0):
            industries=', '.join(list(set(tmp)))
        
        tmp=msig_data["df_market_capital_volume"][msig_data["df_market_capital_volume"]["event_number"]==i+1]["market_capital"].values
        if(len(tmp)>0):
            market_cap="$"+str(round(sum(tmp),2))
        
        if(type(e["leading indicator"])==int):
            eventDateTimeStampEpochs= e["leading indicator"] 
            tmp=int((e["leading indicator"]*bucket_size_msec + min_ts))
            tmp=str(datetime.fromtimestamp(tmp/1000).astimezone(pytz.timezone(timeZone)))  
            start_time=tmp[tmp.find(' ')+1:tmp.rfind('-')]
        
        if(type(e["main indicator"])==int):
            eventDateTimeStampEpochs= e["main indicator"] 
            tmp=int((e["main indicator"]*bucket_size_msec + min_ts))
            tmp=str(datetime.fromtimestamp(tmp/1000).astimezone(pytz.timezone(timeZone)))  
            main_time=tmp[tmp.find(' ')+1:tmp.rfind('-')]
        
        if(type(e["trailing indicator"])==int):
            eventDateTimeStampEpochs= e["trailing indicator"] 
            tmp=int((e["trailing indicator"]*bucket_size_msec + min_ts))
            tmp=str(datetime.fromtimestamp(tmp/1000).astimezone(pytz.timezone(timeZone)))  
            end_time=tmp[tmp.find(' ')+1:tmp.rfind('-')]
        
        tmp=pd.DataFrame(msig_data["df_market_capital_volume"][msig_data["df_market_capital_volume"]["event_number"]==i+1].sort_values(by=["market_capital"],ascending=False))
        tmp=tmp.astype({'volume':'int32'})
        if(len(df_company_news)>0):
            df_event_news=df_company_news[df_company_news["symbol"].isin(list(tmp["symbol"].values))].sort_values(by=["compound"],ascending=False)
            if(category=="GAIN"):
                df_event_news=df_event_news[df_event_news["compound"]>0.05]
                df_event_news["max_compound"]=df_event_news.groupby("symbol")["compound"].transform('max')
                df_event_news=df_event_news[df_event_news["compound"]==df_event_news["max_compound"]].drop(["max_compound"],axis=1)
                df_event_news=df_event_news.drop_duplicates(subset=["newsTitle"],keep="first")
            else:
                df_event_news=df_event_news[df_event_news["compound"]<0]
                df_event_news["min_compound"]=df_event_news.groupby("symbol")["compound"].transform('min')
                df_event_news=df_event_news[df_event_news["compound"]==df_event_news["min_compound"]].drop(["min_compound"],axis=1)
                df_event_news=df_event_news.drop_duplicates(subset=["newsTitle"],keep="last")
            if(len(df_event_news)>0):
               news_snippet="<br> MAGI has found the following news and analyzed them between -1 and 1 related to this event:" 
               for j,n in df_event_news.iterrows():
                   news_snippet=news_snippet+"<li><em>"+str(n["prefix"])+"</em><a href="+str(n["newsLink"])+">"+str(n["newsTitle"])+"</a> (MAGI Score="+str(n["compound"])+").</li>"
                   if(j==50):break
               news_snippet=news_snippet+"<br>" 
 
        companies_table=tmp.to_html(index=False,header=True,columns=['symbol','price','volume','market_capital','indicator_type'],justify='center',na_rep='Unknown', float_format='%10.2f USD')
        companies_table=companies_table.replace('symbol','Symbol')
        companies_table=companies_table.replace('price','Price')
        companies_table=companies_table.replace('volume','Volume')
        companies_table=companies_table.replace('market_capital','Market Capital')
        companies_table=companies_table.replace('indicator_type','Role')
    template="<h3>Here are the details:</h3> \
                <br> \
                <p>MagiFinance detected an event of size <strong>"+str(market_cap)+".</strong>\
                The event seems to affect the <strong>sectors</strong>= <em>"+str(sectors)+"</em>, \
                and the corresponding <strong>industries</strong>=<em>" +str(industries)+".</em><br>\
                The timing of the event is as follows:\
                <li>Starting time of the event @ <strong>"+str(start_time)+"</strong></li>\n \
                <li>Main/peak time of the event @ <strong>"+str(main_time)+"</strong></li>\n \
                <li>Trailing time of the event @ <strong>"+str(end_time)+"</strong></li><br>\
                Please scroll down for related <strong>news</strong> and a <strong>summary table</strong>.\n <br>"+str(news_snippet)+str(companies_table)
    return template


def sendNewsToFrontEnd(msig_data,cli_options,df_market_capital_price,df_market_capital_volume,url = 'http://localhost:5000/Events/PostEvents',num_events_price_gain=0,num_events_volume_gain=0,isStartofDay=False):
    import json
    import requests
    from datetime import datetime
    import pytz
    import redis
    import pandas as pd
    import pickle
    redis_msig=redis.Redis(host=cli_options.msig_host,port=cli_options.msig_port)
    df_company_news=pd.DataFrame()
    df_company_daily_news=pd.DataFrame()
    df_curated_news=pd.DataFrame()
    if(redis_msig.ping()):
        tmp_data=redis_msig.lpop("NewsCompany")
        redis_msig.lpush("NewsCompany",tmp_data)
        if(len(tmp_data)>0):
            tmp_data=pickle.loads(tmp_data)
            #if(tmp_data["date"].split('T')[0]==datetime.today().strftime("%Y-%m-%d")):
            df_company_news=pd.DataFrame(tmp_data["data"])  
    timeZone=cli_options.timeZone
    headers = {'accept': 'application/json'}
    
    df_company_daily_news=getDaily2NewsForEvents(msig_data["df_market_capital_price"],msig_data["indicators_price"],cli_options.L2fileName)
    
    for i,e in msig_data["events_price"].iterrows():
        eventDateTimeStampEpochs=int((e["main indicator"]*cli_options.bucket_size_msec + msig_data["ts_price_min"]))
        tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
        event_type="price"
        if(i<=num_events_price_gain):
            category="GAIN"
            isGain=True
        else:
            category="LOSS"
            isGain=False
        newsTitle="A "+category+ " event based on PRICE detected @ "+ tmp_date[:tmp_date.rfind('-')]
        #print(newsTitle)
        htmlStory=generateHtmlStory(msig_data,i,e,event_type,cli_options.bucket_size_msec,msig_data["ts_price_min"],timeZone,df_company_news,category,df_company_daily_news)
        indicators=[]
        tmp=df_market_capital_price[df_market_capital_price["event_number"]==i+1].sort_values(by="market_capital",ascending=False)
        for j,p in df_market_capital_price[df_market_capital_price["event_number"]==i+1].iterrows():
            if(p["indicator_type"]=="leading indicator"):eventRole="Leading Indicator"
            elif(p["indicator_type"]=="main indicator"):eventRole="Main Indicator"
            else:eventRole="Trailing Indicator"
            indicators.append( {"symbol": p["symbol"],
                                "volume": p["volume"],
                                "price":  p["price"],
                                "eventRole": eventRole})
        htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                  "htmlData": htmlStory,
                  "newsTitle":newsTitle,
                  "indicators":indicators,"eventFlag":"Price",
                  'isGain':isGain}]
        response = requests.post(url,headers=headers,json=htmlData)
        if(response.text):
            print(response.text)
            
    for i,e in msig_data["events_volume"].iterrows():
        eventDateTimeStampEpochs=int((e["main indicator"]*cli_options.bucket_size_msec + msig_data["ts_volume_min"]))
        tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
        event_type="volume"
        if(i<=num_events_volume_gain):
            category="GAIN"
            isGain=True
        else:
            category="LOSS"
            isGain=False
        newsTitle="A "+category+ " event based on VOLUME detected @ "+ tmp_date[:tmp_date.rfind('-')]
        htmlStory=generateHtmlStory(msig_data,i,e,event_type,cli_options.bucket_size_msec,msig_data["ts_volume_min"],timeZone,df_company_news,category)        
        indicators=[]
        tmp=df_market_capital_volume[df_market_capital_volume["event_number"]==i+1].sort_values(by="market_capital",ascending=False)
        for j,p in df_market_capital_volume[df_market_capital_volume["event_number"]==i+1].iterrows():
            if(p["indicator_type"]=="leading indicator"):eventRole="Leading Indicator"
            elif(p["indicator_type"]=="main indicator"):eventRole="Main Indicator"
            else:eventRole="Trailing Indicator"
            indicators.append( {"symbol": p["symbol"],
                                "volume": p["volume"],
                                "price":  p["price"],
                                "eventRole": eventRole})
        htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                  "htmlData": htmlStory,
                  "newsTitle":newsTitle,
                  "indicators":indicators,"eventFlag":"Volume",
                  'isGain':isGain}]

        response = requests.post(url,headers=headers,json=htmlData)
        if(response.text):
            print(response.text)
    #post sector news
    #Tying sector news to the first main time stamp of the price events
    if(redis_msig.ping()):
        tmp_data=redis_msig.lpop("NewsIndustry")
        redis_msig.lpush("NewsIndustry",tmp_data)
        if(len(tmp_data)>0):
            tmp_data=pickle.loads(tmp_data)
        #if(tmp_data["date"].split('T')[0]==datetime.today().strftime("%Y-%m-%d")):
            df_industry_news=pd.DataFrame(tmp_data["data"])
            df_industry_news=df_industry_news.sort_values(by=["compound"],ascending=False)
            df_industry_news=df_industry_news.drop_duplicates(subset=["newsLink"],keep="first")
            if(len(df_industry_news)>0):
                eventDateTimeStampEpochs=msig_data["ts_price_min"]
                tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
                newsTitle="Sector/Industry news and their MAGI Scores @ "+ tmp_date[:tmp_date.rfind('-')]
                htmlStory=""
                z=1
                for k,inews in df_industry_news.iterrows():
                    htmlStory=htmlStory+"<li><strong>"+inews["sector"]+"/"+inews["industry"]+" : </strong><a href="+str(inews["newsLink"])+">"+str(inews["newsTitle"])+"</a> (MAGI Score="+str(inews["compound"])+").</li>"
                    z=z+1
                    if(z==50):break                        
                htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                  "htmlData": htmlStory,
                  "newsTitle":newsTitle,"indicators":[],"eventFlag":"Price"}]
                response = requests.post(url,headers=headers,json=htmlData)
                if(response.text):
                    print(response.text)
    #CURATED NEWS
    curated_topics=cli_options.curatedNews.split(',')
    htmlStory=""
    if(len(curated_topics)>5):
        print("More than 5 topics detected in cratedNews. This will overwhelm the News API. Using only the first 5 topics.")
        curated_topics=curated_topics[:5]
    if(len(curated_topics)>0):
        curated_topics=[str.strip(x) for x in curated_topics]
        df_curated_news=getDailyCuratedNews(curated_topics)
        if(len(df_curated_news)>0):
          eventDateTimeStampEpochs=msig_data["ts_price_min"]-1001
          tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
          newsTitle="Today's Top News & MAGI Scores"
          htmlStory="<strong>Political"+ " News:</strong><br>"
          for k,topnews in df_curated_news.iterrows():
              if(k==5 or k==10):
                  htmlStory=htmlStory+"<br><strong>"+topnews["fullName"]+" News:</strong><br>"+"<li><strong>"+"</strong><a href="+str(topnews["newsLink"])+">"+str(topnews["newsTitle"])+"</a> (MAGI Score="+str(topnews["compound"])+").</li>"
              else:
                  htmlStory=htmlStory+"<li><strong>"+"</strong><a href="+str(topnews["newsLink"])+">"+str(topnews["newsTitle"])+"</a> (MAGI Score="+str(topnews["compound"])+").</li>"
          htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                  "htmlData": htmlStory,
                  "newsTitle":newsTitle,"indicators":[],"eventFlag":"Price"}]
          response = requests.post(url,headers=headers,json=htmlData)
          if(response.text):
              print(response.text)       
    #END CURATED NEWS
           
def sendGainLossToRedis(df_price,df_volume,all_data,events_price_gain,events_price_loss, events_volume_gain, events_volume_loss,indicators_price_gain,indicators_price_loss, indicators_volume_gain, indicators_volume_loss,prefix="rts1:01:symbol:",L2fileName="finL2Extension.graphml",window_size=10,mind_host="localhost",mind_port=6378,bucket_size_msec=60000,ts_min=0,url='http://localhost:5000/Correlations/PostCorrelations'):
    import pandas as pd
    import json
    import requests
    import functools
    import operator
    print("\n(THREAD):Sending correlations to the front end\n")
    headers = {'accept': 'application/json'}
    #Industry and sector correlations
    df_sectors_price_gains,df_sectors_price_loss,df_industries_price_gains,df_industries_price_loss,\
    df_sectors_volume_gains,df_sectors_volume_loss,df_industries_volume_gains,df_industries_volume_loss=generateAllGainLossIndices(df_price,df_volume,all_data["ts_price"][0],all_data["ts_volume"][0],window_size=window_size,prefix=prefix,mind_host=mind_host,mind_port=mind_port,bucket_size_msec=bucket_size_msec,L2fileName=L2fileName)
    
    df_sectors_price_gains_corr=df_sectors_price_gains.corr().round(4)
    if(len(df_sectors_price_gains_corr)>0):
        df_sectors_price_gains_corr=df_sectors_price_gains_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=1*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":"Sector Correlations based on Price GAIN Events",
                               "x":list(df_sectors_price_gains_corr.columns),
                               "y":df_sectors_price_gains_corr.index.values.tolist(),
                               "z":df_sectors_price_gains_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass
    
    df_sectors_price_loss_corr=df_sectors_price_loss.corr().round(4)
    if(len(df_sectors_price_loss_corr)>0):
        df_sectors_price_loss_corr=df_sectors_price_loss_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=events_price_loss.loc[0]["main indicator"]*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":"Sector Correlations based on Price LOSS Events",
                               "x":list(df_sectors_price_loss_corr.columns),
                               "y":df_sectors_price_loss_corr.index.values.tolist(),
                               "z":df_sectors_price_loss_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass    
    df_industries_price_gains_corr=df_industries_price_gains.corr().round(4)
    if(len(df_industries_price_gains_corr)>0):
        df_industries_price_gains_corr=df_industries_price_gains_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=2*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":"Industry Correlations based on Price GAIN Events",
                               "x":list(df_industries_price_gains_corr.columns),
                               "y":df_industries_price_gains_corr.index.values.tolist(),
                               "z":df_industries_price_gains_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass
    
    df_industries_price_loss_corr=df_industries_price_loss.corr().round(4)
    if(len(df_industries_price_loss_corr)>0):
        df_industries_price_loss_corr=df_industries_price_loss_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=3*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":'Industry Correlations based on Price LOSS Events',
                               "x":list(df_industries_price_loss_corr.columns),
                               "y":df_industries_price_loss_corr.index.values.tolist(),
                               "z":df_industries_price_loss_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass
    
    df_sectors_volume_gains_corr=df_sectors_volume_gains.corr().round(4)
    if(len(df_sectors_volume_gains_corr)>0):
        df_sectors_volume_gains_corr=df_sectors_volume_gains_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=4*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":'Sector Correlations based on Volume GAIN Events',
                               "x":list(df_sectors_volume_gains_corr.columns),
                               "y":df_sectors_volume_gains_corr.index.values.tolist(),
                               "z":df_sectors_volume_gains_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass
    
    df_sectors_volume_loss_corr=df_sectors_volume_loss.corr().round(4)
    if(len(df_sectors_volume_loss_corr)>0):
        df_sectors_volume_loss_corr=df_sectors_volume_loss_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=5*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":'Sector Correlations based on Volume LOSS Events',
                               "x":list(df_sectors_volume_loss_corr.columns),
                               "y":df_sectors_volume_loss_corr.index.values.tolist(),
                               "z":df_sectors_volume_loss_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass
    
    df_industries_volume_gains_corr=df_industries_volume_gains.corr().round(4)
    if(len(df_industries_volume_gains_corr)>0):
        df_industries_volume_gains_corr=df_industries_volume_gains_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=6*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":'Industry Correlations based on Volume GAIN Events',
                               "x":list(df_industries_volume_gains_corr.columns),
                               "y":df_industries_volume_gains_corr.index.values.tolist(),
                               "z":df_industries_volume_gains_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass
    
    df_industries_volume_loss_corr=df_industries_volume_loss.corr().round(4)
    if(len(df_industries_volume_loss_corr)>0):
        df_industries_volume_loss_corr=df_industries_volume_loss_corr.fillna(0)
        try:
            correlationDateTimeStampEpochs=7*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                               "title":"Industry Correlations based on Volume LOSS Events",
                               "x":list(df_industries_volume_loss_corr.columns),
                               "y":df_industries_volume_loss_corr.index.values.tolist(),
                               "z":df_industries_volume_loss_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        except Exception as e:
            pass
    col_volume_gain=[]
    col_price_gain=[]
    col_price_loss=[]
    col_volume_loss=[]
    for i,row in indicators_price_gain.iterrows():
        col_price_gain=row.values.tolist()
        col_price_gain=functools.reduce(operator.iconcat, col_price_gain, [])
        col_price_gain=list(set(col_price_gain))
    for i,row in indicators_price_loss.iterrows():
        col_price_loss=row.values.tolist()
        col_price_loss=functools.reduce(operator.iconcat, col_price_loss, [])
        col_price_loss=list(set(col_price_loss))
    for i,row in indicators_volume_gain.iterrows():
        col_volume_gain=row.values.tolist()
        col_volume_gain=functools.reduce(operator.iconcat, col_volume_gain, [])
        col_volume_gain=list(set(col_volume_gain))
    for i,row in indicators_volume_loss.iterrows():
        col_volume_loss=row.values.tolist()
        col_volume_loss=functools.reduce(operator.iconcat, col_volume_loss, [])
        col_volume_loss=list(set(col_volume_loss))   
    
    col_price_gain.extend(col_price_loss)
    col_price_gain=list(set(col_price_gain))

    col_volume_gain.extend(col_volume_loss)
    col_volume_gain=list(set(col_volume_gain))
    
    if(len(col_price_gain)>0):
        df_tmp=df_price[df_price.columns.intersection(col_price_gain)]
        if(len(df_tmp>window_size-1)):
            df_tmp=df_tmp.loc[window_size-1:,:]
            df_corr=df_tmp.corr().round(4)
            df_corr=df_corr.fillna(0)
            correlationDateTimeStampEpochs=bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                       "title":"Company Correlations based on Price Events",
                       "x":list(df_corr.columns),
                       "y":df_corr.index.values.tolist(),
                       "z":df_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
    
    # if(len(col_price_loss)>0):
    #     df_tmp=df_price[df_price.columns.intersection(col_price_loss)]
    #     if(len(df_tmp>window_size-1)):
    #         df_tmp=df_tmp.loc[window_size-1:,:]
    #         df_corr=df_tmp.corr().round(4)
    #         correlationDateTimeStampEpochs=events_price_loss.loc[0]["main indicator"]*bucket_size_msec+ts_min
    #         htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
    #                    "title":"Company Correlations based on Price LOSS Events",
    #                    "x":list(df_corr.columns),
    #                    "y":df_corr.index.values.tolist(),
    #                    "z":df_corr.values.tolist()}]
    #         response = requests.post(url,headers=headers,json=htmlData)
    #         if(response.text):
    #             print(response.text)
 
    if(len(col_volume_gain)>0):
        df_tmp=df_volume[df_volume.columns.intersection(col_volume_gain)]
        if(len(df_tmp>window_size-1)):
            df_tmp=df_tmp.loc[window_size-1:,:]
            df_corr=df_tmp.corr().round(4)
            df_corr=df_corr.fillna(0)
            correlationDateTimeStampEpochs=8*bucket_size_msec+ts_min
            htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
                        "title":"Company Correlations based on Volume Events",
                        "x":list(df_corr.columns),
                        "y":df_corr.index.values.tolist(),
                        "z":df_corr.values.tolist()}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
    
    # if(len(col_volume_loss)>0):
    #     df_tmp=df_volume[df_volume.columns.intersection(col_volume_loss)]
    #     if(len(df_tmp>window_size-1)):
    #         df_tmp=df_tmp.loc[window_size-1:,:]
    #         df_corr=df_tmp.corr().round(4)
    #         correlationDateTimeStampEpochs=events_volume_loss.loc[0]["main indicator"]*bucket_size_msec+ts_min
    #         htmlData=[{"correlationDateTimeStampEpochs":correlationDateTimeStampEpochs,
    #                    "title":"Company Correlations based on Volume LOSS Events",
    #                    "x":list(df_corr.columns),
    #                    "y":df_corr.index.values.tolist(),
    #                    "z":df_corr.values.tolist()}]
    #         response = requests.post(url,headers=headers,json=htmlData)
    #         if(response.text):
    #             print(response.text)    
    print("\n(THREAD):Done!\n")
def generateAllGainLossIndices(df_price,df_volume,ts_price,ts_volume,window_size=10,prefix="rts1:01:symbol:",mind_host="localhost", mind_port=6378,bucket_size_msec=60000,labels={"TYPE":"GAINLOSS"},L2fileName="finL2Extension.graphml"):
    import pandas as pd
    from redistimeseries.client import Client
    import networkx as nx
    import re
    from MIndex_Functions import sendDfToRedis
    G=nx.read_graphml(L2fileName)
    redis_out=Client(host=mind_host,port=mind_port)
    nodes=pd.DataFrame.from_dict(dict(G.nodes(data=True)),orient='index')
    companies=list(nodes['symbol'].values)
     #nodes.index=nodes['symbol']
    sectors=list(nodes.sector.dropna().unique())
    #sectors=[re.sub('[^a-zA-Z0-9]+','',x) for x in sectors]
    industries=list(nodes.industry.dropna().unique())
    #industries=[re.sub('[^a-zA-Z0-9]+','',x) for x in industries]
    lookup_sectors=pd.DataFrame(columns=["sector","industry"])
    start=time.time()
    for category in ["price","volume"]: 
        if(category=="price"):
            ts_data=pd.Series(ts_price)
            df_tmp=df_price
        else:
            ts_data=pd.Series(ts_volume)
            df_tmp=df_volume
        index_gain="mind:gain:"+category+":window:"+str(window_size)
        index_loss="mind:loss:"+category+":window:"+str(window_size)
        index_gainloss="mind:gainloss:"+category+":window:"+str(window_size)
        print("adding data for",index_gain,index_loss,index_gainloss, "port=",mind_port, "category=",category)   
        try:
            #create index if does not exists
            if(redis_out.exists(index_gain)==0):
                _=redis_out.create(index_gain)
                _=redis_out.alter(index_gain,labels=labels)
            if(redis_out.exists(index_loss)==0):
                _=redis_out.create(index_loss)
                _=redis_out.alter(index_loss,labels=labels)
            if(redis_out.exists(index_gainloss)==0):
                _=redis_out.create(index_gainloss)
                _=redis_out.alter(index_gainloss,labels=labels)
            #push data gain
            arr_tuples=tuple(zip(ts_data,df_tmp["normalized_gain"].values.astype(float)))
            arr_tuples=arr_tuples[window_size-1:]
            arr_tuples=[(index_gain,)+xs for xs in arr_tuples]
            _=redis_out.madd(arr_tuples)
            #push data loss
            arr_tuples=tuple(zip(ts_data,df_tmp["normalized_loss"].values.astype(float)))
            arr_tuples=[(index_loss,)+xs for xs in arr_tuples]
            arr_tuples=arr_tuples[window_size-1:]
    
            _=redis_out.madd(arr_tuples)
            #push data gainloss
            arr_tuples=tuple(zip(ts_data,df_tmp["normalized_gainloss"].values.astype(float)))
            arr_tuples=[(index_gainloss,)+xs for xs in arr_tuples]
            arr_tuples=arr_tuples[window_size-1:]
            _=redis_out.madd(arr_tuples)
        except Exception as e:
            print(e)
            
        print("generating sector & industry gain loss for",mind_port, category, " window=",window_size)
        missing=[]
        df_clean_tmp=df_tmp.iloc[:,:-6] #the last 6 cols are gain loss sums  
        if(category=='price'):
            df_sectors_price_gains=pd.DataFrame(np.zeros((len(df_clean_tmp),len(sectors))),columns=sectors)
            df_sectors_price_loss=pd.DataFrame(np.zeros((len(df_clean_tmp),len(sectors))),columns=sectors)
            df_industries_price_gains=pd.DataFrame(np.zeros((len(df_clean_tmp),len(industries))),columns=industries)
            df_industries_price_loss=pd.DataFrame(np.zeros((len(df_clean_tmp),len(industries))),columns=industries)
        else:
            df_sectors_volume_gains=pd.DataFrame(np.zeros((len(df_clean_tmp),len(sectors))),columns=sectors)
            df_sectors_volume_loss=pd.DataFrame(np.zeros((len(df_clean_tmp),len(sectors))),columns=sectors)
            df_industries_volume_gains=pd.DataFrame(np.zeros((len(df_clean_tmp),len(industries))),columns=industries)
            df_industries_volume_loss=pd.DataFrame(np.zeros((len(df_clean_tmp),len(industries))),columns=industries)
        for i,row in df_clean_tmp.iterrows():
            data=row.dropna()
            if(i>=window_size-1):
                for t, val in data.iteritems():
                    try:
                        subg=nx.ego_graph(G,t).nodes(data=True)._nodes
                        _=subg.pop("ticker",None)
                        if(len(subg)==2):_=subg.pop(t,None)
                        sect=''
                        ind=''
                        if('sector' in subg[list(subg.keys())[0]]):
                            sect=subg[list(subg.keys())[0]]['sector']
                        if('industry' in subg[list(subg.keys())[0]]):
                            ind=subg[list(subg.keys())[0]]['industry']
    
                        if(len(sect)>0):
                                 if(val>0):
                                     if(category=='price'):
                                         df_sectors_price_gains.at[i,sect]+=float(val)
                                     else: 
                                         df_sectors_volume_gains.at[i,sect]+=float(val)
                                 elif(val<0):
                                     if(category=='price'):
                                         df_sectors_price_loss.at[i,sect]+=float(val)
                                     else:
                                         df_sectors_volume_loss.at[i,sect]+=float(val)
                        elif(i==window_size):
                             if(t not in missing):missing.append(t)
                        if(len(ind)>0):
                                 if(val>0):
                                     if(category=='price'):
                                         df_industries_price_gains.at[i,ind]+=float(val)
                                     else:
                                         df_industries_volume_gains.at[i,ind]+=float(val)
                                 elif(val<0):
                                     if(category=='price'):
                                         df_industries_price_loss.at[i,ind]+=float(val)
                                     else:
                                         df_industries_volume_loss.at[i,ind]+=float(val)
                                 if(i==window_size):lookup_sectors.loc[len(lookup_sectors)]=[re.sub('[^a-zA-Z0-9]+','',sect) ,re.sub('[^a-zA-Z0-9]+','',ind)]
                        elif(i==window_size):
                            if(t not in missing):missing.append(t)
                    except Exception as e:
                        print(e)
    sendDfToRedis(df_sectors_price_gains,df_sectors_price_loss,df_industries_price_gains,df_industries_price_loss,ts_data,lookup_sectors,category="price",output_redis_host=mind_host,output_redis_port=mind_port,window=window_size)
    sendDfToRedis(df_sectors_volume_gains,df_sectors_volume_loss,df_industries_volume_gains,df_industries_volume_loss,ts_data,lookup_sectors,category="volume",output_redis_host=mind_host,output_redis_port=mind_port,window=window_size)

    print("cannot find companies in L2file=",missing)
    print("Index generation done in sec=",time.time()-start)
    return df_sectors_price_gains,df_sectors_price_loss,df_industries_price_gains,df_industries_price_loss,df_sectors_volume_gains,df_sectors_volume_loss,df_industries_volume_gains,df_industries_volume_loss
                
def getEventsFromGainLoss(all_data,window_size=10,enablePlotting=False,gainLossEventRatio=0.05,gainLossIndicatorThreshold=0.025,mind_host="localhost",mind_port=6378,bucket_size_msec=60000,ts_min=0,prefix="rts1:01:symbol:",L2fileName="finL2Extension.graphml"):
    import pandas as pd
    import matplotlib.pyplot as plt
    from sklearn.linear_model import LinearRegression
    import numpy as np
    from scipy.signal import find_peaks, peak_prominences
    column_names=["leading indicator","main indicator","trailing indicator"]
    df_price=pd.DataFrame(all_data["df_price_data"])
    df_volume=pd.DataFrame(all_data["df_volume_data"])
    df_price=df_price.pct_change(window_size-1)
    df_volume=df_volume.pct_change(window_size-1)
    df_market_capital=df_volume*df_price
    df_price["gain"]=df_price.apply(lambda x: x[x>0].sum(),axis=1)
    df_price["loss"]=df_price.apply(lambda x: x[x<0].sum(),axis=1)
    df_price["gainloss"]=df_price["gain"]+df_price["loss"].abs()
    df_price["normalized_gain"]=(df_price["gain"]-df_price["gain"].min())/(df_price["gain"].max()-df_price["gain"].min())
    df_price["normalized_loss"]=(df_price["loss"]-df_price["loss"].min())/(df_price["loss"].max()-df_price["loss"].min())
    df_price["normalized_gainloss"]=(df_price["gainloss"]-df_price["gainloss"].min())/(df_price["gainloss"].max()-df_price["gainloss"].min())
    df_volume["gain"]=df_volume.apply(lambda x: x[x>0].sum(),axis=1)
    df_volume["loss"]=df_volume.apply(lambda x: x[x<0].sum(),axis=1)
    df_volume["gainloss"]=df_volume["gain"]+df_volume["loss"].abs()
    df_volume["normalized_gain"]=(df_volume["gain"]-df_volume["gain"].min())/(df_volume["gain"].max()-df_volume["gain"].min())
    df_volume["normalized_loss"]=(df_volume["loss"]-df_volume["loss"].min())/(df_volume["loss"].max()-df_volume["loss"].min())
    df_volume["normalized_gainloss"]=(df_volume["gainloss"]-df_volume["gainloss"].min())/(df_volume["gainloss"].max()-df_volume["gainloss"].min())
    
    X=np.array(df_price["normalized_gain"])
    peaks,properties=find_peaks(X,prominence=(gainLossEventRatio,1))
    if(enablePlotting):
        prominences=peak_prominences(X, peaks)[0]
        countour_heights=X[peaks]-prominences
        plt.plot(X)
        plt.title("price: normalized_gain")
        plt.plot(peaks,X[peaks],'x',color='red')
        plt.vlines(x=peaks, ymin=countour_heights, ymax=X[peaks],color='black')
        plt.figure()
    peaks=peaks.astype(object)
    dict_tmp={"leading indicator":properties["left_bases"].astype(object),"main indicator":peaks,"trailing indicator":properties["right_bases"].astype(object)}
    events_price_gain=pd.DataFrame(dict_tmp)
    df=pd.DataFrame(df_price.iloc[:,:-6])
    indicators_price_gain=getIndicatorsFromGainLoss(events_price_gain,df,window_size,'gain',gainLossIndicatorThreshold)
    
    X=np.array(df_price["normalized_loss"])
    peaks,properties=find_peaks(X,prominence=(gainLossEventRatio,1))
    if(enablePlotting):
        prominences=peak_prominences(X, peaks)[0]
        countour_heights=X[peaks]-prominences
        plt.plot(X)
        plt.title("price: normalized_loss")
        plt.plot(peaks,X[peaks],'x',color='red')
        plt.vlines(x=peaks, ymin=countour_heights, ymax=X[peaks],color='black')
        plt.figure()
    peaks=peaks.astype(object)
    dict_tmp={"leading indicator":properties["left_bases"].astype(object),"main indicator":peaks,"trailing indicator":properties["right_bases"].astype(object)}
    events_price_loss=pd.DataFrame(dict_tmp,columns=column_names)
    df=pd.DataFrame(df_price.iloc[:,:-6])
    indicators_price_loss=getIndicatorsFromGainLoss(events_price_loss,df,window_size,'loss',gainLossIndicatorThreshold)

    event_control=True 
    volume_ratio=gainLossEventRatio
    X=np.array(df_volume["normalized_gain"])
    while(event_control):
        peaks,properties=find_peaks(X,prominence=(volume_ratio,1))
        if(len(peaks)>20):
            volume_ratio=volume_ratio+gainLossEventRatio
        else:
            event_control=False
    if(enablePlotting):
        prominences=peak_prominences(X, peaks)[0]
        countour_heights=X[peaks]-prominences
        plt.plot(X)
        plt.title("volume: normalized_gain")
        plt.plot(peaks,X[peaks],'x',color='red')
        plt.vlines(x=peaks, ymin=countour_heights, ymax=X[peaks],color='black')
        plt.figure()
    peaks=peaks.astype(object)
    dict_tmp={"leading indicator":properties["left_bases"].astype(object),"main indicator":peaks,"trailing indicator":properties["right_bases"].astype(object)}
    events_volume_gain=pd.DataFrame(dict_tmp,columns=column_names)
    #df=pd.DataFrame(df_volume.iloc[:,:-6])
    df=pd.DataFrame(df_market_capital)
    indicators_volume_gain=getIndicatorsFromGainLoss(events_volume_gain,df,window_size,'gain',gainLossIndicatorThreshold*20)
    
    event_control=True 
    volume_ratio=gainLossEventRatio
    X=np.array(df_volume["normalized_loss"])
    while(event_control):
        peaks,properties=find_peaks(X,prominence=(volume_ratio,1))
        if(len(peaks)>20):
            volume_ratio=volume_ratio+gainLossEventRatio
        else:
            event_control=False    
    if(enablePlotting):
        prominences=peak_prominences(X, peaks)[0]
        countour_heights=X[peaks]-prominences
        plt.plot(X)
        plt.title("volume: normalized_loss")
        plt.plot(peaks,X[peaks],'x',color='red')
        plt.vlines(x=peaks, ymin=countour_heights, ymax=X[peaks],color='black')
        plt.figure()
    peaks=peaks.astype(object)
    dict_tmp={"leading indicator":properties["left_bases"].astype(object),"main indicator":peaks,"trailing indicator":properties["right_bases"].astype(object)}
    events_volume_loss=pd.DataFrame(dict_tmp,columns=column_names)
    #df=pd.DataFrame(df_volume.iloc[:,:-6])
    df=pd.DataFrame(df_market_capital)
    indicators_volume_loss=getIndicatorsFromGainLoss(events_volume_loss,df,window_size,'loss',gainLossIndicatorThreshold*20)
    print("Initiating an asynch thread to send indices to Redis and correlations to Front End.")
    import threading
    #sendGainLossToRedis(df_price,df_volume,all_data,events_price_gain,events_price_loss, events_volume_gain, events_volume_loss,indicators_price_gain,indicators_price_loss, indicators_volume_gain, indicators_volume_loss,window_size,mind_host,mind_port,bucket_size_msec,ts_min,prefix=prefix,L2fileName=L2fileName)
    if(len(df_price)>0 and len(events_price_gain)>0):
        thr=threading.Thread(target=sendGainLossToRedis,args=(df_price,df_volume,all_data,events_price_gain,events_price_loss, events_volume_gain, events_volume_loss,indicators_price_gain,indicators_price_loss, indicators_volume_gain, indicators_volume_loss,prefix,L2fileName,window_size,mind_host,mind_port,bucket_size_msec,ts_min,))
        thr.start()
    return events_price_gain,events_price_loss, events_volume_gain, events_volume_loss,indicators_price_gain,indicators_price_loss, indicators_volume_gain, indicators_volume_loss   


def getIndicatorsFromGainLoss(events_price_gain,df,window_size,category='gain',gainLossIndicatorThreshold=0.05): 
    import pandas as pd     
    li=[]
    mi=[]
    ti=[]
    for i,r in events_price_gain.iterrows():
        l=int(r["leading indicator"])
        m=int(r["main indicator"])
        t=int(r["trailing indicator"])
        tmp_l=[]
        tmp_m=[]
        tmp_t=[]
        if(l>=window_size-1 and l<len(df)-1):
           df_row=pd.DataFrame(df.iloc[l,:])
           if(category=='gain'):
                df_row=df_row[df_row>=gainLossIndicatorThreshold].dropna() 
                if(len(df_row)<1):
                    df_row=pd.DataFrame(df.iloc[l,:]).sort_values(by=[l],ascending=False).head(5)                   
           else:
                df_row=df_row[df_row<=-gainLossIndicatorThreshold].dropna()
                if(len(df_row)<1):
                    df_row=pd.DataFrame(df.iloc[l,:]).sort_values(by=[l],ascending=True).head(5)
           tmp_l=df_row.index.tolist() 
     
        if(m>=window_size-1 and m<len(df)-1):
            df_row=pd.DataFrame(df.iloc[m,:])
            if(category=='gain'):
                df_row=df_row[df_row>=gainLossIndicatorThreshold].dropna()
                if(len(df_row)<1):
                    df_row=pd.DataFrame(df.iloc[m,:]).sort_values(by=[m],ascending=False).head(5)
            else:
                df_row=df_row[df_row<=-gainLossIndicatorThreshold].dropna()  
                if(len(df_row)<1):
                    df_row=pd.DataFrame(df.iloc[m,:]).sort_values(by=[m],ascending=True).head(5)
            tmp_m=df_row.index.tolist()
            
        if(t>=window_size-1 and t<len(df)-1):  
            df_row=pd.DataFrame(df.iloc[t,:])
            if(category=='gain'):
                df_row=df_row[df_row>=gainLossIndicatorThreshold].dropna()
                if(len(df_row)<1):
                    df_row=pd.DataFrame(df.iloc[t,:]).sort_values(by=[t],ascending=False).head(5)
            else:
                df_row=df_row[df_row<=-gainLossIndicatorThreshold].dropna()
                if(len(df_row)<1):
                    df_row=pd.DataFrame(df.iloc[t,:]).sort_values(by=[t],ascending=True).head(5)
            tmp_t=df_row.index.tolist()
        
        li.append(tmp_l)
        mi.append(tmp_m)
        ti.append(tmp_t)
        
    indicators=pd.DataFrame({"li":li,"mi":mi,"ti":ti})
    return indicators


if __name__ == "__main__":
     pass






