import redis
import pandas as pd
import numpy as np
import sys
import os
from typing import List
import argparse
import json
import time
if "MSIG_MYSQL_PASS" in os.environ:
    MSIG_MYSQL_PASS=os.environ["MSIG_MYSQL_PASS"]
else:
    print("Unable to read environment variable MSIG_MYSQL_PASS...")
    MSIG_MYSQL_PASS=""
_=np.seterr(all="ignore")
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from pathlib import Path
msig_path=os.path.realpath('__file__').split('/')[0:-2]
msig_path.extend(["MSig"])
sys.path.append(os.path.realpath(Path( os.path.realpath("/".join(msig_path)))))
import redis
from redistimeseries.client import Client 
import MSig_Functions as MSig
def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--msig_host',
        type=str,
        default='localhost',
        help='redis host for signal output'
    )
    parser.add_argument(
        '--msig_port',
        type=int,
        default=6380,
        help='redis port for signal output'
    )
    parser.add_argument(
        '--msig_output',
        type=str,
        default="msig:output",
        help='msig output redis stream name'
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
        default='MModel',
        help='mysql database for signal output'
    )
    parser.add_argument(
        '--mysql_pass',
        type=str,
        default=MSIG_MYSQL_PASS,
        help='mysql password for signal output. Default is set to the environment variable $MSIG_MYSQL_PASS'
    )
    parser.add_argument(
    '--input_ports',
    dest = 'input_ports',
    default = [item for item in range(6400,6470)],
    nargs = '+',
    type =list,
    help='list of port reading backlog data'

    )
    parser.add_argument(
    '--start_port_order',
    dest = 'start_port_order',
    default = 0,
    type =int,
    help='starting port for bulk processing. Bigger end-start number can cause memory issues. zero based'
    )
    parser.add_argument(
    '--end_port_order',
    dest = 'end_port_order',
    default = 5,
    type =int,
    help='end port for bulk processing. Bigger end-start number can cause memory issues. Not including this number'
    )
    parser.add_argument(
        '--bucket_size_msec',
        type=int,
        default=60000,
        help='aggregation bucket size in msec for time series'
    )
    return parser
def getBestPredictiveModel(cols:list,events:pd.DataFrame,all_regimes:pd.DataFrame,first_timestamp,last_timestamp,bucket_size_msec):
    from sklearn.metrics import precision_recall_fscore_support
    from sklearn.metrics import confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    import random
    """This function tests multiple models to come with the best predictive power. 
    TODO: This is an optimization algorithm to be done by another agent. ANN models fail significantly. 
    KNN Regressor works great but lacks predictive power. 2nd best is RandomForestClassifier"""
    #train a model 
   
    #TODO!:This is an optimization problem. Another agent should try all and find the best model#
    X, y = df_predictive.iloc[:,:-1].values.astype('int'),df_predictive.iloc[:,-1].values.astype('int')
    while(True):
        random_state=random.randint(0, 1000)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=random_state)
        if(1 in y_test):break
    
    print("Running KNeighbors Regressor...")
     #KNeighborsRegressor
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.metrics import precision_recall_fscore_support
    from sklearn.metrics import confusion_matrix
    neigh = KNeighborsRegressor(n_neighbors=2,algorithm='kd_tree')
    neigh=neigh.fit(X_train, y_train)
    y_pred=neigh.predict(X_test)   
    y_pred=y_pred+0.0001
    y_pred=y_pred.round()
    m=confusion_matrix(y_test, y_pred)
    print("Precision Recall and F1 Score for KNN Regressor")
    print(precision_recall_fscore_support(y_test, y_pred,average='weighted'))
    
    #TODO! : KNN regressor cannot give predictive power per indicator. We switched manually to 
    print("Running RandomForestClassifier...")
    clf = RandomForestClassifier(max_depth=100, random_state=1)
    clf=clf.fit(X_train, y_train)
    y_pred=clf.predict(X_test)
    m=confusion_matrix(y_test, y_pred)
    print(precision_recall_fscore_support(y_test, y_pred,average='weighted'))    
    from treeinterpreter import treeinterpreter as ti
    prediction, bias, contributions = ti.predict(clf, X_test)
    
    #we guessed all the 1's
    tmp_contrib=[]
    for i in range(len(prediction)):
        if(prediction[i][1]>prediction[i][0]):
            print("Instance", i)
            print("Bias (trainset mean)", bias[i])
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
    df_event_contributor=df_event_contributor.groupby('event').count()    
    from sklearn import svm
    clf=svm.SVC(kernel="rbf")
    clf=clf.fit(X_train,y_train)
    y_pred=clf.predict(X_test)
    m=confusion_matrix(y_test, y_pred)
    m
   
    return df_event_contributor,[]
 
    
def addLabelsToRedis(ports=list(range(6400,6470)),refHost='localhost',refPort=6381,labels={"SYMSET":"ACTIVE"}):
    rts = Client(host=refHost, port=refPort)
    resp=rts.execute_command("keys *", filters=labels)
    for target in ports:
        rts = Client(host=refHost, port=target)
        print("Labeling price and volume keys on port="+str(target))
        for k in resp:
            try:
                target_keys=rts.execute_command("keys *")
                if(k in target_keys and ("price" in str(k) or "volume" in str(k))):
                    _=rts.alter(k,labels=labels)
            except Exception as e:
                print(e)
                print(target,k)
                
def getTrainingDataFromDF(cols:list,events:pd.DataFrame,all_regimes:pd.DataFrame,first_timestamp,last_timestamp,bucket_size_msec=60000):
    
    cols=list(cols)
    df_regimes=pd.DataFrame(all_regimes)
    #Predictive power
    #print("Preparing the dataset for training")
    cols.append('event')
    df_predictive=np.zeros((int(abs((last_timestamp-first_timestamp))/bucket_size_msec),int(len(cols))),dtype=int)
    df_predictive=pd.DataFrame(df_predictive,columns=cols)    
    # for i in range(len(cols)):
    #     data=[0]*len(df_predictive.columns)
    #     df_predictive.loc[i]=data
    for j,reg in df_regimes.iterrows():
        r=list(reg)
        r=[int(x) for x in r if (str(x) !="nan")]
        for k in r:
            df_predictive[list(df_predictive.columns)[int(j)]][k]=1

    for i,row in events.iterrows():
        m=row["main indicator"]
        df_predictive['event'][m]=1
    return df_predictive
        
def main(args: List[str]) -> None:
    parser = get_cli_parser()
    cli_options = parser.parse_args(args)
    #read all training data
    redis_msig=redis.Redis(host=cli_options.msig_host,port=cli_options.msig_port)
    mmodel_data=""
    print("Reading redis stream")
    session_start=time.time()
    mmodel_data=redis_msig.xread({cli_options.msig_output:0},count=None)
    ids=[]
    event_data=[]
    #df_volume_predictions=pd.DataFrame()
    df_price_predictions=pd.DataFrame()

    #create data frames before split training data
    if(len(mmodel_data)>0):
        print("Preparing the dataset for training")
        for i in range(60,70):
            d=mmodel_data[0][1][i]
            ids.append(str(d[0])[1:])
            tmp=json.loads(d[1].get(b"data"))
            for k,v in tmp.items():
                if(type(v)==dict):
                    tmp[k]=pd.DataFrame(v) 
            #event_data.append(tmp)
            df_tmp_price=getTrainingDataFromDF(cols=list(tmp["price_columns"]),events=tmp["events_price"],all_regimes=tmp["regimes_price"],first_timestamp=tmp["ts_price_min"],last_timestamp=tmp["ts_price_max"],bucket_size_msec=cli_options.bucket_size_msec)
            df_price_predictions=pd.concat([df_price_predictions,df_tmp_price],axis=0)
            
            #df_tmp_volume=getTrainingDataFromDF(tmp["volume_columns"],tmp["events_volume"],tmp["regimes_volume"])
            #df_volume_predictions=df_volume_predictions.append(df_tmp_volume,ignore_index=True)
            #print(len(df_price_predictions),len(df_volume_predictions))
        #df_price_predictions.to_csv("withNA.csv",index=False,header=True)
        df_price_predictions=df_price_predictions.fillna(0)
        reorder=df_price_predictions.pop('event')
        df_price_predictions['event']=reorder
        #df_price_predictions.to_csv("withoutNA.sv",index=False,header=True)
    
    from sklearn.metrics import precision_recall_fscore_support
    from sklearn.metrics import confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    import random    
    # while(True): #make sure we have events in the test set because number of events are too low
    #     random_state=random.randint(0, 1000)
    #     X=np.array(df_price_predictions.iloc[:,:-1].values.astype('int'))
    #     y=np.array(df_price_predictions.iloc[:,-1].values.astype('int'))
    #     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=random_state)
    #     if(1 in y_test):break
    X, y = df_price_predictions.iloc[:,:-1].values.astype('int'),df_price_predictions.iloc[:,-1].values.astype('int')
    split_point=int(len(X)*0.8)
    X_train=X[:split_point,:]
    X_test=X[split_point:,:]
    y_train=y[:split_point]
    y_test =y[split_point:] 
 #TODO! : KNN regressor cannot give predictive power per indicator. We switched manually to 
    print("Running RandomForestClassifier...")
    clf = RandomForestClassifier(max_depth=200,random_state=1,n_jobs=-1)
    clf=clf.fit(X_train, y_train)
    y_pred=clf.predict(X_test)
    m=confusion_matrix(y_test, y_pred)
    print(m)
    print(precision_recall_fscore_support(y_test, y_pred,average='weighted'))    
    
    from treeinterpreter import treeinterpreter as ti
    prediction, bias, contributions = ti.predict(clf, X_test)
    #we guessed some of the 1's
    tmp_contrib=[]
    for i in range(len(prediction)):
         if(prediction[i][1]>prediction[i][0]):
             print("Instance", i)
             print("Bias (trainset mean)", bias[i])
             tmp_contrib.append(contributions[i])

    df_event_contributor=pd.DataFrame(columns=['contribution','li name','event'])    
    event=1
    for c in tmp_contrib:
        for i in range(len(c)):
            if(c[i][1]!=0):
                 contribution=abs(c[i][1])
                 li_name=df_price_predictions.columns[i]
                 df_event_contributor.loc[len(df_event_contributor)]=[contribution,li_name,event]
        event=event+1
    
    df_event_contributor=df_event_contributor.sort_values(['event', 'contribution'], ascending=[True, False])       
    #contributors=df_event_contributor.to_csv("contributors.csv",index=False,header=True)
    #df_event_contributor.groupby('event').count()
    #df_event_contributor.to_csv("output",index=False,header=True)
    # all_data=MSig.get_data_from_mrF(redis_port=cli_options.input_ports[0])

def adjustTestData(df_testd_price,df_price_days):
    train_cols_not_in_test= list(df_price_days.columns.difference(df_testd_price.columns))   
    test_cols_not_in_traing=list(df_testd_price.columns.difference(df_price_days.columns))
    #delete the test cols not in training
    for t in test_cols_not_in_traing:
        df_testd_price.drop(t,axis=1)
    
    # add missing columns from training to test
    for m in train_cols_not_in_test:
        df_testd_price[m]=pd.DataFrame(np.zeros(shape=(len(df_testd_price),1)),index=df_testd_price.index)
     
    reorder=df_testd_price.pop('event')
    df_testd_price['event']=reorder
    
    return df_testd_price

def analyzePorts(args: List[str]):
    from sklearn.metrics import precision_recall_fscore_support
    from sklearn.metrics import confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import LinearSVC
    from xgboost import XGBClassifier
    from sklearn.naive_bayes import ComplementNB
    import random    
    parser = get_cli_parser()
    cli_options = parser.parse_args(args)
    #read all training data
    redis_msig=redis.Redis(host=cli_options.msig_host,port=cli_options.msig_port)
    mmodel_data=""
    print("Reading redis stream")
    session_start=time.time()
    mmodel_data=redis_msig.xread({cli_options.msig_output:0},count=None)
    test_days=[]
    train_days=[]
    #test and train days days
    if(len(mmodel_data)>0):
        print("Preparing the dataset for testing")
        for i in range(60,70):
            d=mmodel_data[0][1][i]
            tmp=json.loads(d[1].get(b"data"))
            for k,v in tmp.items():
                if(type(v)==dict):
                    tmp[k]=pd.DataFrame(v) 
            test_days.append(tmp) #adding test days temporally ordered
    
        print("Preparing the dataset for training")
        for i in range(0,60):
            d=mmodel_data[0][1][i]
            tmp=json.loads(d[1].get(b"data"))
            for k,v in tmp.items():
                if(type(v)==dict):
                    tmp[k]=pd.DataFrame(v) 
            train_days.append(tmp) 
    results=[]
    train_patterns=[1,2,5,10,15,20,30,40,45,60]
    for p in train_patterns:
        print("training days:",p)
        #get the last p days of training set and construct
        subset_train_data=train_days[-p:]
        df_price_days=pd.DataFrame()
        #construct training data from that
        for day in subset_train_data:
            df_tmp_price=getTrainingDataFromDF(cols=list(day["price_columns"]),events=day["events_price"],all_regimes=day["regimes_price"],first_timestamp=day["ts_price_min"],last_timestamp=day["ts_price_max"],bucket_size_msec=cli_options.bucket_size_msec)
            df_price_days=pd.concat([df_price_days,df_tmp_price],axis=0)
        #deal with introduced empty cols due to NAN, sort the arrays
        df_price_days=df_price_days.fillna(0)
        df_price_days=df_price_days.reindex(sorted(df_price_days.columns),axis=1)
        reorder=df_price_days.pop('event')
        df_price_days['event']=reorder
        #df_price_days.to_csv("60daysData.csv",index=False,header=True)
        a=np.array([0,1])
        X_train, y_train = df_price_days.iloc[:,:-1].values.astype('int'),df_price_days.iloc[:,-1].values.astype('int')
        #Train the model
        #print("training random forest")
        #clf = RandomForestClassifier(max_depth=200,random_state=1,n_jobs=-1)
        #clf=clf.fit(X_train, y_train)
        print("training linear svm")
        svm_c=LinearSVC(max_iter=10000)
        svm_c=svm_c.fit(X_train, y_train)
        print("training complement nb")
        nb=ComplementNB()
        nb=nb.fit(X_train, y_train)
        print("training xgboost")
        xgb=XGBClassifier(predictor='gpu_predictor')
        xgb=xgb.fit(X_train, y_train)
        #test
        cnt_day=10
        df_tmp_test=pd.DataFrame()
        df_testd_price=pd.DataFrame()
        print("constructing & aligning test data")
        for testd in test_days:
            df_tmp_test=getTrainingDataFromDF(cols=list(testd["price_columns"]),events=testd["events_price"],all_regimes=testd["regimes_price"],first_timestamp=testd["ts_price_min"],last_timestamp=testd["ts_price_max"],bucket_size_msec=cli_options.bucket_size_msec)
            df_tmp_test=adjustTestData(df_tmp_test,df_price_days)
            df_testd_price=pd.concat([df_testd_price,df_tmp_test],axis=0)
        df_testd_price=df_testd_price.fillna(0)
        df_testd_price=df_testd_price.reindex(sorted(df_testd_price.columns),axis=1)
        reorder=df_testd_price.pop('event')
        df_testd_price['event']=reorder
        #df_tmp.to_csv("10daysTesting.csv",index=False,header=True)
        X_test, y_test=df_testd_price.iloc[:,:-1].values.astype('int'),df_testd_price.iloc[:,-1].values.astype('int')
        try:
            y_pred=svm_c.predict(X_test)
            y_test_labeled=['event' if i==1 else 'no_event' for i in y_test]
            y_pred_labeled=['event' if i==1 else 'no_event' for i in y_pred]
            m=confusion_matrix(y_test_labeled, y_pred_labeled,labels=['event','no_event'])
            s=precision_recall_fscore_support(y_test_labeled, y_pred_labeled,labels=['event'],zero_division=0)
            tp=m[0][0]
            fp=m[1][0]
            tn=m[1][1]
            fn=m[0][1]
            params={'model':"Linear SVM",'train days':p,'test day':cnt_day,"confusion_matrix":m,"tp":tp,"fp":fp,"tn":tn,"fn":fn,"precision":s[0][0],"recall":s[1][0],"f1":s[2][0]}
            results.append(params)
            
            y_pred=nb.predict(X_test)
            y_test_labeled=['event' if i==1 else 'no_event' for i in y_test]
            y_pred_labeled=['event' if i==1 else 'no_event' for i in y_pred]
            m=confusion_matrix(y_test_labeled, y_pred_labeled,labels=['event','no_event'])
            s=precision_recall_fscore_support(y_test_labeled, y_pred_labeled,labels=['event'],zero_division=0)
            tp=m[0][0]
            fp=m[1][0]
            tn=m[1][1]
            fn=m[0][1]
            params={'model':"Complement Naive Bayes",'train days':p,'test day':cnt_day,"confusion_matrix":m,"tp":tp,"fp":fp,"tn":tn,"fn":fn,"precision":s[0][0],"recall":s[1][0],"f1":s[2][0]}
            results.append(params)
            
            y_pred=xgb.predict(X_test)
            y_test_labeled=['event' if i==1 else 'no_event' for i in y_test]
            y_pred_labeled=['event' if i==1 else 'no_event' for i in y_pred]
            m=confusion_matrix(y_test_labeled, y_pred_labeled,labels=['event','no_event'])
            s=precision_recall_fscore_support(y_test_labeled, y_pred_labeled,labels=['event'],zero_division=0)
            tp=m[0][0]
            fp=m[1][0]
            tn=m[1][1]
            fn=m[0][1]
            params={'model':"XGBoost",'train days':p,'test day':cnt_day,"confusion_matrix":m,"tp":tp,"fp":fp,"tn":tn,"fn":fn,"precision":s[0][0],"recall":s[1][0],"f1":s[2][0]}
            results.append(params)
            
        except Exception as e:
            print("skipping",p,cnt_day)
        
    df=pd.DataFrame(results)
    # for i,row in df.iterrows():
    #     precision=row["scores"][0]
    #     recall=row["scores"][1]
    #     f1=row["scores"][2]
    #     m=row["confusion_matrix"]
    #     TN, FP, FN, TP =m.ravel()
    #     event_guessed=float(m[1][1]/(m[1][0]+m[1][1]))
    #     no_event_guessed=float(m[0][0]/(m[0][1]+m[0][0]))
    #     df.loc[i,"precision"]=precision
    #     df.loc[i,"recall"]=recall
    #     df.loc[i,"f1"]=f1
    #     df.loc[i,"% events detected succ"]=event_guessed
    #     df.loc[i,"% no-events succ"]=no_event_guessed
    #     df.loc[i,"TN"]=TN
    #     df.loc[i,"TP"]=TP
    #     df.loc[i,"FP"]=FP
    #     df.loc[i,"FN"]=FN
    df.to_csv("70days_performances2.csv",index=False,header=True)
        
     
if __name__ == "__main__":
    pass
    #addLabelsToRedis()
    #main(sys.argv[1:])
#cols=mmodel_data["price_columns"]
#events=mmodel_data["events_price"]
#all_regimes=mmodel_data["regimes_price"]