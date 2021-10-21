def loadDataToRedis(host='localhost',port=6379, fname="20200712_Hawkeye.csv",labels={"TARGET":"SENSORDOG"}):
    from redistimeseries.client import Client
    import pandas as pd
    df=pd.read_csv(fname)
    rts = Client(host=host, port=port)
    timeStamps=df.iloc[:,0].values.astype(float)
    timeStamps=[int(x) for x in timeStamps]
    for i in range(1, len(df.columns)):
        #ts_name='ts'+str(i)
        ts_name=df.columns[i]
        #Create time series
        try:
            _=rts.create(ts_name, labels=labels)
        except:
            _=rts.execute_command("del "+ts_name)
            _=rts.create(ts_name, labels=labels)
        #Create array of key, ts, value tuples
        arr_ktv=tuple(zip(timeStamps, df.iloc[:,i].values.astype(float)))
        arr_ktv=[(ts_name,)+xs for xs in arr_ktv]
        _=rts.madd(arr_ktv)
    _=rts.execute_command("save")
    return

def getDataFromRedis(host="localhost",port=6379,from_time=0,to_time=-1,aggregation_type="last",bucket_size_msec=60000, filters=["TARGET=SENSORDOG"],enablePercentChange=True):
    from redistimeseries.client import Client
    import time
    import pandas as pd
    all_data={}
    rts = Client(host=host, port=port)
    ts_min=[]
    ts_max=[]
    ts_all=[]
    data_all=[]
    keys_all=[]
    try:
        print("Querying from Redis database...")
        start=time.time()
        bulk_data=rts.mrange(from_time=from_time,to_time=to_time,aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
        print(round(time.time()-start,2), "sec for retrieving",len(bulk_data),"time series")
        print("Preparing dataframe from query result...")
        for d in bulk_data:
            key=str(list(d.keys())[0]) #name of time series
            rest=list(d.get(key))[1]
            if(len(rest)>0):
                ts,data = map(list,zip(*rest)) # timestamps and data
                ts_min.extend(ts)
                ts_min=[min(ts_min)]
                ts_max.extend(ts)
                ts_max=[max(ts_max)]
                ts_all.append(ts)
                data_all.append(data)
                keys_all.append(key)
        print("Done")
        df=pd.DataFrame(data_all)
        df=df.transpose()
        df.columns=keys_all
        if(enablePercentChange):
            df=df.pct_change()
            df=df[1:]
            for l in ts_all:
                del l[0]
            ts_min=[min(map(min,ts_all))]
            ts_max=[max(map(max,ts_all))]
        all_data={"ts_all":ts_all,"df":df,"ts_min":ts_min[0],"ts_max":ts_max[0]}
        return all_data
    except Exception as e:
        print(e)
        return {}

def clusterTs(df):
    import time
    import timeSeriesL1Analytics
    """
    This function receives a data frame of time series. Analyzes them and returns initial clusters:
        lines - constant slope time series are not interesting
        squares - stair-like square signals dont look like contributing to events
        spikes - spike like signal can be event triggers. Need further analysis. 
    """
    start=time.time()
    print("Filtering lines, squares and spikes from time series")
    df,df_lines=timeSeriesL1Analytics.filter_lines(df)
    df,df_spikes=timeSeriesL1Analytics.filter_spikes(df)
    df_spquares,df_spikes=timeSeriesL1Analytics.splitSquaresFromSpikes(df_spikes)
    print(int(time.time()-start), "sec. for successfully filtering")
    return df, df_lines,df_spquares,df_spikes

def getHistogramsFromMP(df,num_regimes=20, window=10,isRemoveFirstFalsePositive=False):
    """This function receives a df of time series. Uses matrix profiles to find regime changes.
    Creates a histogram form the regime changes across all time series"""
    import matrixprofile as mp
    import numpy as np
    np.warnings.filterwarnings('ignore')
    import pandas as pd
    import time
    import timeSeriesL1Analytics
    #Matrix profile
    timings_mp=[]    
    timings_fluss=[]
    all_regimes=[]
    print("Running matrix profile to get regime changes...")
    start_all=time.time()
    for i in range(len(df.columns)):
        ts=df.iloc[:,i]
        ts=ts[ts.notnull()].values.astype(np.float32)
        start_time = time.time()
        profile=mp.compute(ts,windows=[window],n_jobs=-1)
        timings_mp.append(time.time()-start_time)
        start_time = time.time()
        x=mp.discover.regimes(profile, num_regimes=num_regimes)
        timings_fluss.append(time.time()-start_time)
        regimes= list(filter(lambda x: x != 0, x["regimes"]))
        regimes= list(filter(lambda x: x != len(df), regimes))
        all_regimes.append(regimes)
    histogram=timeSeriesL1Analytics.getHistogramFromDf(pd.DataFrame(all_regimes), len(df))
    print(round(time.time()-start_all,2), "sec of total time....",round(sum(timings_mp),2), " for MP computation,",round(sum(timings_fluss),2), "for semantic seg")
    if(isRemoveFirstFalsePositive): histogram[window]=1
    return histogram, all_regimes  
  
def plotEventsOnHistogram(histogram,number_of_samples,events):
    import matplotlib.pyplot as plt
    from scipy import interpolate
    import numpy as np
    """This function viusalizes events on the histogram of regime changes"""
    plt.bar(range(number_of_samples),histogram,width=3)
    for i,row in events.iterrows():
        start_event=row[0]
        end_event=row[2]
        peek=row[1]
        x=[start_event,peek,end_event]
        y=[0,histogram[peek],0]
        x2 = np.linspace(x[0], x[-1], 1000)
        y2 = interpolate.pchip_interpolate(x, y, x2)
        plt.plot(x2, y2)
    plt.show()
    
def printEventStats(time_stamps,indicators,events,timeZone='US/Pacific'):
    """This function prints the number of indicators per event & time stats"""
    #event stats
    import pytz
    tz=pytz.timezone(timeZone)
    import datetime
    date_time_stamps=[str(datetime.datetime.fromtimestamp(int(i/1000)).astimezone(tz)) for i in time_stamps]
    print("Event# \t #LeadingIndicators \t #MainIndicators \t #TrailingIndicators")
    for i, row in indicators.iterrows():
        print(i+1, "\t",len(row["leading indicators"]),"\t",len(row["main indicators"]),"\t",len(row["trailing indicators"]))
    
    print("Event# \t #L.I.DateTime \t\t\t\t #M.I.DateTime \t\t\t\t #T.I.DateTime")
    for i, row in events.iterrows():
        print(i+1,"\t",date_time_stamps[int(row["leading indicator"])],"\t",date_time_stamps[int(row["main indicator"])],"\t",date_time_stamps[int(row["trailing indicator"])])

def getIndicators(events,df,all_regimes):
    """Given events and a df of time series, this function creates df of indicators for each event"""
    import pandas as pd
    ts_names=list(df.columns)
    mi=[]
    li=[]
    ti=[]
    for i,r in events.iterrows():
        l=r["leading indicator"]
        m=r["main indicator"]
        t=r["trailing indicator"]
        tmp_l=[]
        tmp_m=[]
        tmp_t=[]
        counter=0
        for temp_r in all_regimes:
            if(l in temp_r and ts_names[counter] not in tmp_l):
                tmp_l.append(ts_names[counter])
            elif(m in temp_r and ts_names[counter] not in tmp_m):
                tmp_m.append(ts_names[counter])
            elif(t in temp_r and ts_names[counter] not in tmp_t):
                tmp_t.append(ts_names[counter])
            counter=counter+1
        li.append(tmp_l)
        mi.append(tmp_m)
        ti.append(tmp_t)  
    indicators=pd.DataFrame({"leading indicators":li,"main indicators":mi,"trailing indicators":ti})  
    return indicators

def getBestPredictiveModel(events,df,all_regimes):
    """This function tests multiple models to come with the best predictive power. 
    TODO: This is an optimization algorithm to be done by another agent. ANN models fail significantly. 
    KNN Regressor works great but lacks predictive power. 2nd best is RandomForestClassifier"""
    import time
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from treeinterpreter import treeinterpreter as ti #Check shap explainable ai 
    from sklearn.metrics import precision_recall_fscore_support
    import pandas as pd
    #train a model 
    df_regimes=pd.DataFrame(all_regimes)
    #Predictive power
    print("Preparing the dataset for training")
    start=time.time()
    cols=list(df.columns)
    cols.append('event')
    df_predictive=pd.DataFrame(columns=cols)    
    for i in range(len(df)):
        data=[0]*len(df_predictive.columns)
        df_predictive.loc[i]=data
    for j,reg in df_regimes.iterrows():
        r=list(reg)
        r=[int(x) for x in r if (str(x) !="nan")]
        for k in r:
            df_predictive[df_predictive.columns[j]][k]=1
    for i,row in events.iterrows():
        m=row["main indicator"]
        df_predictive['event'][m]=1
    print(round(time.time()-start,2), "sec. for successful data preparation")
    #TODO!:This is an optimization problem. Another agent should try all and find the best model#
    X, y = df_predictive.iloc[:,:-1].values.astype('int'),df_predictive.iloc[:,-1].values.astype('int')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=0)
    print("Running RandomForestClassifier...")
    clf = RandomForestClassifier(max_depth=200, random_state=0,n_jobs=-1)
    clf=clf.fit(X_train, y_train)
    y_pred=clf.predict(X_test)
    from sklearn.metrics import confusion_matrix
    y_test_labeled=['event' if i==1 else 'no_event' for i in y_test]
    y_pred_labeled=['event' if i==1 else 'no_event' for i in y_pred]
    m=confusion_matrix(y_test_labeled, y_pred_labeled,labels=['event','no_event'])
    tp=m[0][0]
    if(tp==0):
        print("Model could not predict events. Trying XGBoost")
        from xgboost import XGBClassifier
        try:
            xgb=XGBClassifier(predictor="gpu_predictor",n_jobs=-1)
        except Exception as e:
            print("GPU not detected. Using CPU.")
            xgb=XGBClassifier(n_jobs=-1)
        xgb=xgb.fit(X_train, y_train)
        y_pred=xgb.predict(X_test)
        y_test_labeled=['event' if i==1 else 'no_event' for i in y_test]
        y_pred_labeled=['event' if i==1 else 'no_event' for i in y_pred]
        m=confusion_matrix(y_test_labeled, y_pred_labeled,labels=['event','no_event'])

    print("Confusion matrix")
    print(m)
    tp=m[0][0]
    fp=m[1][0]
    tn=m[1][1]
    fn=m[0][1]
    s=precision_recall_fscore_support(y_test_labeled,y_pred_labeled,labels=['event'],zero_division=0)
    print("TP:",tp,"FP:",fp,'TN:',tn,'FN:',fn)
    print("Based on events, Precision:",s[0][0],"Recall:",s[1][0],"F1:",s[2][0])
    print("Calculating predictive power of time series...")
    prediction, bias, contributions = ti.predict(clf, X_test)
    #we guessed all the 1's
    tmp_contrib=[]
    for i in range(len(prediction)):
        if(prediction[i][1]>prediction[i][0]):
            #print("Instance", i)
            #print("Bias (trainset mean)", bias[i])
            tmp_contrib.append(contributions[i])

    df_event_contributor=pd.DataFrame(columns=['contribution','li name','event'])    
    event=1
    for c in tmp_contrib:
        for i in range(len(c)):
            if(c[i][1]!=0):
                contribution=abs(c[i][1])
                li_name=df_predictive.columns[i]
                df_event_contributor.loc[len(df_event_contributor)]=[contribution,li_name,event]
        event=event+1
    
    df_event_contributor=df_event_contributor.sort_values(['event', 'contribution'], ascending=[True, False])       
    df_event_contributor.groupby('event').count()    
    return df_event_contributor

def generateCorrelations(df_plotly,isDisplay=True,title='Correlations'):
    import plotly.graph_objects as go
    import plotly.io as pio
    import plotly
    import pandas as pd
    from datetime import datetime
    import re
    pio.renderers.default='browser'
    def df_to_ploty(df):
        return {'z':df.values.tolist(),
                'x':df.columns.tolist(),
                'y':df.index.tolist()}
    fig=go.Figure(data=go.Heatmap(df_to_ploty(df_plotly.corr())))
    fig.update_layout(title_text=title,title_x=0.5,title_y=0)
    fig.update_xaxes(side='top')
    fig.update_yaxes(autorange='reversed')
    if(isDisplay):fig.show()
    title=title+"_"+re.sub(r'\W+','_',str(datetime.now()))
    plotly.offline.plot(fig,filename=title+'.html',auto_open=False)
    

def createDashBoards(events,indicators,df_event_contributor,ts_all):
    pass












