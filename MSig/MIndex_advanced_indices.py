import numpy as np
_=np.seterr(all="ignore")
import datetime
import MSig_Functions

def get_data_from_MIndF(redis_host="localhost",redis_port=6378,from_time=0,to_time=-1,filters=["CATEGORY=INDUSTRY","SUBTYPE=GAIN","BASEDON=PRICE"],window=10,bucket_size_msec=0):
    from redistimeseries.client import Client
    import time
    import pandas as pd
    all_data={}
    rts = Client(host=redis_host, port=redis_port)
    ts_list=[]
    ts_min=[]
    ts_max=[]
    data_list=[]
    key_list=[]
    from_time=int(to_time)
    to_time=int(from_time)
    filters.append("WINDOW="+str(window))
    try:
          print("Querying indices...")
          start=time.time()
          bulk_data=rts.mrange(from_time=from_time,to_time=to_time, filters=filters,bucket_size_msec=bucket_size_msec)
          print("Querying completed:",int(time.time()-start),"sec.")
          print("Preparing data...")
          start=time.time()
          for d in bulk_data:
              key=str(list(d.keys())[0]) #name of time series
              rest=list(d.get(key))[1]
              if(len(rest)>0):
                  ts,data = map(list,zip(*rest)) # timestamps and data
                  ts_min.extend(ts) 
                  ts_min=[min(ts_min)]
                  ts_max.extend(ts)
                  ts_max=[max(ts_max)]
                  ts_list.append(ts)
                  data_list.append(data)
                  key_list.append(key.split(":")[2])
          print("Data preparation completed:",int(time.time()-start),"sec.")
    except Exception as e:
        print(e)    
    df_data=pd.DataFrame(data_list)
    df_data=df_data.transpose()
    df_data.columns=key_list
    if(len(ts_min)==0):
        return dict()
    else:
        all_data={"ts_list":ts_list,"df_data":df_data,"ts_min":ts_min[0],"ts_max":ts_max[0],"window":window}
        return all_data

def pearsonCor():
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import scipy.stats as stats

    overall_pearson_r = all_data["df_data"].corr()
    overall_pearson_r.to_csv("CorrelationsVolumeLossIndustryWindow10.csv")
    print(f"Pandas computed Pearson r: {overall_pearson_r}")
    # out: Pandas computed Pearson r: 0.2058774513561943

    r, p = stats.pearsonr(all_data["df_data"].iloc[:,0].values, all_data["df_data"].iloc[:,1])
    print(f"Scipy computed Pearson r: {r} and p-value: {p}")
    # out: Scipy computed Pearson r: 0.20587745135619354 and p-value: 3.7902989479463397e-51
    
    # Compute rolling window synchrony
    f,ax=plt.subplots(figsize=(7,3))
    all_data["df_data"].iloc[:,0:2].rolling(window=30,center=True).median().plot(ax=ax)
    ax.set(xlabel='Time',ylabel='Pearson r')
    ax.set(title=f"Overall Pearson r = {np.round(overall_pearson_r,2)}");

def crosscorr(datax, datay, lag=0, wrap=False):
    """ Lag-N cross correlation. 
    Shifted data filled with NaNs 
    
    Parameters
    ----------
    lag : int, default 0
    datax, datay : pandas.Series objects of equal length
    Returns
    ----------
    crosscorr : float
    """
    if(wrap):
        shiftedy = datay.shift(lag)
        shiftedy.iloc[:lag] = datay.iloc[-lag:].values
        return datax.corr(shiftedy)
    else: 
        return datax.corr(datay.shift(lag))

def WTLCC(all_data):
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    # d1 = all_data["df_data"]['AerospaceDefense']
    # d2 = all_data["df_data"]['AssetManagement']
    # seconds = 5
    # fps = 50
    # rs = [crosscorr(d1,d2, lag) for lag in range(-int(seconds*fps),int(seconds*fps+1))]
    # offset = np.ceil(len(rs)/2)-np.argmax(rs)
    # f,ax=plt.subplots(figsize=(14,3))
    # ax.plot(rs)
    # ax.axvline(np.ceil(len(rs)/2),color='k',linestyle='--',label='Center')
    # ax.axvline(np.argmax(rs),color='r',linestyle='--',label='Peak synchrony')
    # #ax.set(title=f'Offset = {offset} frames\nS1 leads <> S2 leads',ylim=[.1,.31],xlim=[0,301], xlabel='Offset',ylabel='Pearson r')
    # #ax.set_xticks([0, 50, 100, 151, 201, 251, 301])
    # #ax.set_xticklabels([-150, -100, -50, 0, 50, 100, 150]);
    # plt.legend()

    # Windowed time lagged cross correlation
    seconds = 5
    fps = 10
    no_splits = 50
    samples_per_split = all_data["df_data"].shape[0]/no_splits
    rss=[]
    for t in range(0, no_splits):
        d1 = all_data["df_data"]['Leisure'].loc[(t)*samples_per_split:(t+1)*samples_per_split]
        d2 = all_data["df_data"]['TravelServices'].loc[(t)*samples_per_split:(t+1)*samples_per_split]
        rs = [crosscorr(d1,d2, lag) for lag in range(-int(seconds*fps),int(seconds*fps+1))]
        rss.append(rs)
    rss = pd.DataFrame(rss)
    f,ax = plt.subplots(figsize=(10,5))
    sns.heatmap(rss,cmap='RdBu_r',ax=ax)
    ax.set(title=f'Leisure  /  Windowed Time Lagged Cross Correlation  /  TravelServices', xlabel='Offset',ylabel='Window epochs')
    #ax.set_xticks([0, 50, 100, 151, 201, 251, 301])
    #ax.set_xticklabels([-150, -100, -50, 0, 50, 100, 150]);

def alphaBeta(ports=[item for item in range(6400,6465)],redis_host="localhost",redis_port=6378,from_time=0,to_time=-1,l1File="finL2Extension.graphml",aggregation_type="last",bucket_size_msec=60000,filters=["SYMSET=ACTIVE"]):
 
    import networkx as nx
    import pandas as pd
    from scipy import stats
    import numpy as np
    import pandas_datareader as web
    from datetime import date, datetime
    import time
    for p in ports:
        all_data=MSig_Functions.get_data_from_mrF(redis_host=redis_host,redis_port=p,from_time=from_time,to_time=to_time,filters=filters,aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec)
    x=time.time()
    
    # for t in tickers:
    #     prices=web.DataReader(tickers,'yahoo','2020-11-13 06:30','2020-11-13 13:30')
    #     break
    print(time.time()-x)

def generateDailyCorrelations(redis_host="localhost",redis_port=6378, start_date=datetime.datetime.strptime('2020-06-20 06:30:00.0','%Y-%m-%d %H:%M:%S.%f'),end_date=datetime.datetime.now(), category='INDUSTRY',subtype='GAIN', basedon='PRICE',include_loss=True,window=10,tz='US/Pacific'):
    #filters=["CATEGORY=INDUSTRY","SUBTYPE=GAIN","BASEDON=PRICE"]
    from pytz import timezone
    tz=timezone('US/Pacific')
    from redistimeseries.client import Client
    import time
    import pandas as pd
    from datetime import timedelta
    rts = Client(host=redis_host, port=redis_port)
    start=datetime.date(start_date.year,start_date.month,start_date.day)
    end=datetime.date(end_date.year,end_date.month,end_date.day)
    day=datetime.timedelta(days=1)
    while(start<=end):
        from_time=datetime.datetime.combine(start,datetime.time(6,30))
        to_time=datetime.datetime.combine(start,datetime.time(13,0))
        to_time=int(datetime.datetime.timestamp(to_time)*1000)
        from_time=int(datetime.datetime.timestamp()*1000)
        filters=["CATEGORY="+category,"SUBTYPE="+subtype,"BASEDON="+basedon]
        all_data=get_data_from_MIndF(redis_host,redis_port,to_time,from_time,filters,window)
        if(len(all_data)>0):
            break
        start=start+day
def saveHeatMap(df_corr,date,category='price',sub_type='correlation',display=False):
    import plotly.graph_objects as go
    import plotly.io as pio
    import plotly
    pio.renderers.default='browser'
    def df_to_plotly(df):
        return {'z': df.values.tolist(),
                'x': df.columns.tolist(),
                'y': df.index.tolist()}
    fig = go.Figure(data=go.Heatmap(df_to_plotly(df_corr)))
    fig.update_layout(title_text=category+"-"+str(date),title_x=0.5)
    fig.update_xaxes(side='top')
    fig.update_yaxes(autorange='reversed')
    if(display):fig.show()
    plotly.offline.plot(fig, filename = 'outp/'+category+"-"+str(date)+'.html', auto_open=False)
def getEventsFromGain(key='mind:gain:price:window:10',redis_host="localhost",redis_port=6378, start_date=datetime.datetime.strptime('2020-06-22 06:30:00.0','%Y-%m-%d %H:%M:%S.%f'),end_date=datetime.datetime.strptime('2020-06-22 13:30:00.0','%Y-%m-%d %H:%M:%S.%f'),window=10,tz='US/Pacific'):
    from pytz import timezone
    tzinfo=timezone(tz)
    from redistimeseries.client import Client
    import pandas as pd
    import matplotlib.pyplot as plt
    from sklearn.linear_model import LinearRegression
    import numpy as np
    from scipy.signal import find_peaks, peak_prominences
    rts = Client(host=redis_host, port=redis_port) 
    from_time=int(datetime.datetime.timestamp(start_date)*1000)
    to_time=int(datetime.datetime.timestamp(end_date)*1000)
    if(rts.ping()==False):
        print("unable to reach redis at", redis_host,redis_port)
        return
    outp=rts.range(key,from_time=from_time,to_time=to_time)
    if(len(outp)<1):
        print("No data found. Check the parameters.")
        return
    ts,data = map(list,zip(*outp))
    # model=LinearRegression()
    # X=[i for i in range(0,len(data))]
    # X=np.reshape(X,(len(X),1))
    # model=model.fit(X,data)
    # trend=model.predict(X)
    # plt.plot(trend)
    # plt.plot(data)
    # plt.show()
    # detrended=[data[i]-trend[i] for i in range(0,len(data))]
    # plt.plot(detrended)
    # plt.bar([i for i in range(0,len(data))],detrended)
    # plt.show()
    X=np.array(data)
    peaks,properties=find_peaks(X,prominence=(None,1))
    prominences=peak_prominences(X, peaks)[0]
    countour_heights=X[peaks]-prominences
    plt.plot(X)
    plt.title(key+" "+str(start_date))
    plt.plot(peaks,X[peaks],'x',color='red')
    plt.vlines(x=peaks, ymin=countour_heights, ymax=X[peaks],color='black')
    plt.show()
    
if __name__ == "__main__":
    pass
    redis_host="localhost"
    redis_port=6378
    from_time=0
    to_time=-1
    filters=["CATEGORY=INDUSTRY","SUBTYPE=GAIN","BASEDON=PRICE"]
    window=10
    all_data=get_data_from_MIndF(redis_host,redis_port,from_time,to_time,filters,window)
    from redistimeseries.client import Client
    rts = Client(host=redis_host, port=redis_port) 
    x=rts.range("mind:industry:MortgageFinance:gain:price:window:10",from_time=1592833140000,to_time=1604697000000)
    15928331400004
    ymd=str(datetime.datetime.fromtimestamp(1592833140000/1000,tz=tz))
    # overall_pearson_r = all_data["df_data"].corr()
     # getHeatMap(overall_pearson_r)
     # filters=["CATEGORY=INDUSTRY","SUBTYPE=GAIN","BASEDON=VOLUME"]
     # all_data_gain=get_data_from_MIndF(redis_host,redis_port,from_time,to_time,filters,window)
     # filters=["CATEGORY=INDUSTRY","SUBTYPE=LOSS","BASEDON=VOLUME"]
     # all_data_loss=get_data_from_MIndF(redis_host,redis_port,from_time,to_time,filters,window)
     
     # df=pd.DataFrame(all_data_gain["df_data"])
     # cols=list(df.columns)
     # cols=[i+"_GAIN" for i in cols]
     # df.columns=cols
     
     # df2=pd.DataFrame(all_data_loss["df_data"])
     # cols=list(df2.columns)
     # cols=[i+"_LOSS" for i in cols]
     # df2.columns=cols
     # df3=pd.concat([df,df2],axis=1)
     # corr=df3.corr()
     # corr.to_csv("CorrelationsVolumeGainLossIndustryWindow10.csv")
     
     # from statsmodels.tsa.stattools import grangercausalitytests
     # x=all_data["df_data"][["Gambling", "Airlines"]]
     # x1=np.diff(x["Gambling"].values)[1:]
     # x2=np.diff(x["Airlines"].values)[1:]
     # x=np.column_stack((x1,x2))
     # res = grangercausalitytests(x,maxlag=5,verbose=True)

    
        #1602792600000
        #.split(' ')[0]

        # if(query_key==None):
        #     #all_keys=r.execute_command("keys *")
        #     print("Querying data...")
        #     start=time.time()
        #     bulk_data=rts.mrange(from_time=from_time,to_time=to_time,aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
        #     print("Querying completed:",int(time.time()-start),"sec.")
        #     print("Splitting data into price and volume...")
        #     for d in bulk_data:
        #         key=str(list(d.keys())[0]) #name of time series
        #         rest=list(d.get(key))[1]
        #         ts,data = map(list,zip(*rest)) # timestamps and data
        #         if(prefix in key and "price" in key):
        #             ts_price_min.extend(ts) 
        #             ts_price_min.extend(ts)
        #             ts_price_min=[min(ts_price_min)]
        #             ts_price_max.extend(ts)
        #             ts_price_max=[max(ts_price_max)]
        #             ts_price.append(ts)
        #             data_price.append(data)
        #             keys_price.append(key.split(":")[3]) 
        #         elif(prefix in key and "volume" in key):
        #             ts_volume_min.extend(ts) 
        #             ts_volume_min.extend(ts)
        #             ts_volume_min=[min(ts_volume_min)]
        #             ts_volume_max.extend(ts)
        #             ts_volume_max=[max(ts_volume_max)]
        #             ts_volume.append(ts)
        #             data_volume.append(data)
        #             keys_volume.append(key.split(":")[3])
    
    # print("Splitting completed.")
    # df_price_data=pd.DataFrame(data_price)
    # df_price_data=df_price_data.transpose()
    # df_price_data.columns=keys_price
    # df_volume_data=pd.DataFrame(data_volume)
    # df_volume_data=df_volume_data.transpose()
    # df_volume_data.columns=keys_volume
    # all_data={"ts_price":ts_price,"df_price_data":df_price_data,"ts_price_min":ts_price_min[0],"ts_price_max":ts_price_max[0],"ts_volume":ts_volume,"df_volume_data":df_volume_data,"ts_volume_min":ts_volume_min[0],"ts_volume_max":ts_volume_max[0]}
    # return all_data