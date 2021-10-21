import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Optional
import pandasql as pdsql
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import scipy
from math import sqrt,pi
from scipy import optimize



def gaussian(x, amplitude, mean, stddev):
    return amplitude * np.exp(-((x - mean) / 16 / stddev)**2)

def plotEventHistograms(histogram_cnt:list,number_of_samples:int,events:pd.DataFrame)->None:
              
    plt.plot(range(number_of_samples),histogram_cnt)
    for i,row in events.iterrows():
        start_event=row[0]
        end_event=row[2]
        peek=row[1]
        x_values = np.linspace(0, number_of_samples, 1000)
        plt.plot(x_values,gaussian(x_values,histogram_cnt[peek],peek,(end_event+start_event)/(end_event-start_event)))
    plt.show()
    return

def getMatrixProfile(ts:np.ndarray,isFigures:bool):
    """This function receives an array of numbers, performs matrix profile analysis on it"""
    """Returns discord, top 3 motifs and corresponding 6 figures for various window sizes"""
    import os
    import numpy as np
    #np raises error for missing values due to sampling error in ts
    np.seterr(all='ignore')
    try:
        import matrixprofile as mp
    except ImportError:
        print("Trying to Install required module: matrixprofile\n")
        os.system('python -m pip install matrixprofile')
        import matrixprofile as mp
    profile, figures = mp.analyze(ts,n_jobs=-1)
    if(isFigures):
        return profile,figures
    else:
        return profile

def cleanAlignmentValues(df:pd.DataFrame, alignmentValue:int):
    """This function receives a set of time series and cleans the alignment value in it"""
    import numpy as np
    df=df.replace(alignmentValue,np.NaN)
    return df

def normalizeTimeSeries(df:pd.DataFrame):
    """This function receives a time series dataframe and normalizes columns."""
    """It returns the normalized dataframe and df composed of horizontal lines"""
    import numpy as np
    np.seterr(all='raise')
    new_df=pd.DataFrame()
    horizontal_cluster=pd.DataFrame()
    for i in range(len(df.columns)):
        tmp=df.iloc[:, i]
        min_val=np.nanmin(tmp.values)
        max_val=np.nanmax(tmp.values)
        if(min_val!=max_val):
            tmp=(tmp - min_val) / (max_val-min_val)
            new_df.insert(len(new_df.columns),tmp.name,tmp)
        else:
            horizontal_cluster.insert(len(horizontal_cluster.columns),tmp.name,tmp)
    return new_df,horizontal_cluster

def filter_lines(df:pd.DataFrame):
    """This function receives a pandas dataframe of time series and removes the lines (constant slopes).
    Each column is a normalized time series data."""
    import numpy as np
    new_df=pd.DataFrame()
    line_cluster=pd.DataFrame()
    for i in range(len(df.columns)):
        #Derivative of the time series
        dTs=np.gradient(df.iloc[:, i].values)
        min_val=np.nanmin(dTs)
        max_val=np.nanmax(dTs)
        tmp=df.iloc[:, i]
        if(min_val != max_val): #not constant slope
            new_df.insert(len(new_df.columns),tmp.name,tmp)
        else:
            line_cluster.insert(len(line_cluster.columns),tmp.name,tmp)
    return new_df,line_cluster

def filter_spikes(df:pd.DataFrame):
    """This function received a dataframe and removes spike signals (=all valus are 0 or 1)."""
    """first return argument is non-spike signals, the second one for the spikes"""
    new_df=pd.DataFrame()
    spike_cluster=pd.DataFrame()
    for i in range(len(df.columns)):
        tmp=df.iloc[:, i] 
        uniques=tmp.unique()
        uniques = [x for x in uniques if str(x) != 'nan']
        uniques = [x for x in uniques if x not in [0.0,1.0]]
        if(len(uniques)<=1): #spike like
            spike_cluster.insert(len(spike_cluster.columns),tmp.name,tmp)
        else:
            new_df.insert(len(new_df.columns),tmp.name,tmp)
    return new_df,spike_cluster

def filter_no_structuralBreaks(df:pd.DataFrame, strucBreaks:list,split_limit:int):
    """This function received a dataframe, and an array of sbreaks' locations 
    and removes signals that have no structural breaks"""
    subset_df=pd.DataFrame()
    cluster_3=pd.DataFrame()
    for i in range(len(df.columns)):
        tmp=df.iloc[:, i] 
        if(len(strucBreaks[i])>0 and len(strucBreaks[i])<split_limit):
           subset_df.insert(len(subset_df.columns),tmp.name,tmp)
        else:
           cluster_3.insert(len(cluster_3.columns),tmp.name,tmp)
    strucBreaks = [x for x in strucBreaks if x != [] and len(x)<split_limit]
    return subset_df, cluster_3,strucBreaks

def plot_ts(subset_df, col_start, col_end, ts_start,ts_end):
    """This function receives a pandas dataframe and returns the line plot of data between given ranges"""
    fig=subset_df.iloc[ts_start:ts_end,col_start:col_end].plot.line(legend=False).get_figure()
    return fig

def get_strucBreaks_R(values):
    import os
    """This function receives a numpy array of time series. Connects to R.
    Detects and returns structural break points in x-axis."""
    #os.environ['R_HOME'] = 'C:\Program Files\R\R-3.6.3'
    try:
        import rpy2.robjects as ro
    except ImportError:
        print("Trying to Install required module: rpy2\n")
        print("Maker sure R is installed and R_HOME environment variable is set...")
        os.system('python -m pip install rpy2')
        import rpy2.robjects as ro
    rstring="""
    function(testdata){
        library(strucchange)
        bpts<-breakpoints(testdata ~ 1)
        bpts
    }
    """
    rdata=ro.vectors.FloatVector(values) #convert to r values
    c=ro.r('c') #concatenate
    ts=ro.r('ts') #time series
    rfunc=ro.r(rstring)
    try:
        r_resp=str(rfunc(c(ts(rdata)))).split()
    except Exception as ex:
        print(ex)
        strucchange=ro.r('install.packages("strucchange")')
        r_resp=str(rfunc(c(ts(rdata)))).split()
    start_ind=r_resp.index("number:")
    end_ind=r_resp.index("Corresponding")
    r_resp=r_resp[start_ind+1:end_ind]
    if(len(r_resp)>0 and 'NA' not in r_resp[0]):
        r_resp=[int(i) for i in r_resp]
    else: 
        r_resp=[]
    return r_resp

def binarySplitBreaks(dfObj:pd.DataFrame,splitCriterion_start:int,splitCriterion_end:int, col:int):
    """This function receives a df of structural break for multiple time series. 
    Splits the df according to the split criteria for the break's location"""
    import math
    smaller_breaks=pd.DataFrame(columns=dfObj.columns)
    larger_breaks=pd.DataFrame(columns=dfObj.columns)
    for index, row in dfObj.iterrows():
        l=list(row)
        if(math.isnan(l[col])==False):
            if(splitCriterion_start<=l[col] and l[col] <=splitCriterion_end):
                smaller_breaks.loc[len(smaller_breaks)]=l
            else:
                larger_breaks.loc[len(larger_breaks)]=l
    return larger_breaks,smaller_breaks

def binarySplitDf(remaining:pd.DataFrame,splitCriterion_start:int, splitCriterion_end:int,col:int, breaks_df:pd.DataFrame):
    """This function receives a df of time series and a df of structural breaks for multiple time series. 
    Splits the the time series df according to the split criteria using the breaks_df"""
    import numpy as np
    strucBreaks=[]
    for index, rows in breaks_df.iterrows():
        strucBreaks.append(rows.to_list())
    strucBreaks=[[int(x) for x in y if not np.isnan(x)] for y in strucBreaks]
    smaller_df=pd.DataFrame()
    larger_df=pd.DataFrame()
    for i in range(len(remaining.columns)):
        lst_b=strucBreaks[i]
        tmp=remaining.iloc[:, i] 
        if(splitCriterion_start<=lst_b[col] and lst_b[col] <=splitCriterion_end):
            smaller_df.insert(len(smaller_df.columns),tmp.name,tmp)
        else:
            larger_df.insert(len(larger_df.columns),tmp.name,tmp)
    return larger_df,smaller_df


def splitSquaresFromSpikes(spike_cluster:pd.DataFrame):
    """This function receives a df with mixed square and spike signals.
    It splits them and returns the two separate sets"""
    squares_df=pd.DataFrame()
    spikes_df=pd.DataFrame()
    for i in range(len(spike_cluster.columns)):
        added=False
        tmp=spike_cluster.iloc[:,i]
        arr=tmp.values.tolist()
        for i in range(len(arr)-1):
            val1=arr[i]
            val2=arr[i+1]
            if(val1 != [] and val2 != []):
                if(val1>0 and val2>0):
                    squares_df.insert(len(squares_df.columns),tmp.name,tmp)
                    added=True
                    break
        if(not added):
            spikes_df.insert(len(spikes_df.columns),tmp.name,tmp)
    return squares_df,spikes_df

def addIntralayerLinkNode(G:nx.Graph, l2FromNode:str, l2ToNode:str, l2TimeSeriesList:list, start_bk:int, end_bk:int)->nx.Graph():
    """This function adds a node representing intralayer links between L2 and L1 time series names """
    l2ToNode=l2ToNode+":"+l2FromNode
    #If we already have a list of intralayer links, add them to that list
    if(G.has_edge(l2FromNode,l2ToNode)):
        a=list(nx.get_node_attributes(G,'L1List')[l2ToNode])
        l2TimeSeriesList.extend(a)
    else:
        G.add_edge(l2FromNode,l2ToNode)
    G.nodes[l2ToNode]['L1List']=l2TimeSeriesList
    G.nodes[l2ToNode]['ts_count']=len(l2TimeSeriesList)
    if(end_bk>0):
        G.nodes[l2ToNode]['break_start']=start_bk
        G.nodes[l2ToNode]['break_end']=end_bk  
    return G

def get_strucBreaks_ruptures(df:pd.DataFrame(),model:str,min_val:int,jum_val:int,pen_val:int)->list:
    """This function receives a df of time series and model parameters. 
    Returns a matrix of structural breaks.
    model:l1, l2, rbf
    """
    import ruptures as rpt
    strucBreaks=[]
    for i in range(len(df.columns)):
        signal=df.iloc[:,i].values
        algo = rpt.Pelt(model=model, min_size=min_val, jump=jum_val).fit(signal)
        my_bkps = algo.predict(pen=pen_val)
        strucBreaks.append(my_bkps)
    return strucBreaks

def removeFPBreaks(df:pd.DataFrame,strucBreaks:list, model:str)->list:
    import chowTest
    """This function receives a df of time series and structural breaks.
    It eliminates false positives by applying Chow Test and model equation comparison"""
    #TODO: Implement for l2 and rbf models
    newBreaks=strucBreaks
    if(model=='l1'): 
        newBreaks=[]
        for i in range(len(df.columns)):
            line=[]
            cnt=0
            breaks=strucBreaks
            ts=df.iloc[:,i].values.tolist()
            for br in breaks:
                x1=ts[0:br]
                x1=list(range(0, br))
                x2=list(range(0, len(ts)-br))
                y1=ts[0:br]
                y2=ts[br:]
                p=chowTest.p_value(y1,x1,y2,x2)
                if(p<0.05):
                    line.append(br)
                else:
                    cnt=cnt+1
            if(cnt>0):
                print(cnt, "break(s) removed for failing the Chow Test for the time series #", i+1)
            newBreaks.append(line)
        newBreaks_phase2=[]
        for i in range(len(df.columns)):
            line_eq=get_ts_mbl(df.iloc[:,i],newBreaks[i])
            tmp_break=[]
            cnt=0
            for j in range(len(line_eq)-1):
                m1=line_eq[j][0]
                b1=line_eq[j][1]
                m2=line_eq[j+1][0]
                b2=line_eq[j+1][1]
                if(min(m1,m2)*0.05 + min(m1,m2) >= max(m1,m2) and min(b1,b2)*0.05 + min(b1,b2) >= max(b1,b2)):
                    cnt=cnt+1
                else:
                    tmp_break.append(newBreaks[i][j])
            if(cnt>0):
                print(cnt, "break(s) removed for failing  for", model, " model check for time series #", i+1)
            newBreaks_phase2.append(tmp_break)
        newBreaks=newBreaks_phase2
    return newBreaks

def get_ts_mbl(ts:pd.DataFrame, breaks:list):
    import math
    """This functions receives a singe time series and corresponding list of breaks.
    Returns a list of m,b,l for each lines for each interval"""
    ts=ts.values.tolist()
    line_eq=[]
    start_ind=0
    for i in range(len(breaks)):
        end_ind=breaks[i]
        x=list(range(start_ind, end_ind))
        y=ts[start_ind:end_ind]
        m,b=np.polynomial.polynomial.polyfit(x,y,1)
        l=math.pow(math.pow((end_ind-start_ind)*m+b,2) +math.pow((end_ind-start_ind),2),0.5)
        line_eq.append([m,b,l])
        start_ind=end_ind
    end_ind=len(ts)-1
    x=list(range(start_ind, end_ind))
    y=ts[start_ind:end_ind]
    m,b=np.polynomial.polynomial.polyfit(x,y,1)
    l=math.pow(math.pow((end_ind-start_ind)*m+b,2) +math.pow((end_ind-start_ind),2),0.5)
    line_eq.append([m,b,l])
    return line_eq

def getFStats(values:list,breaks:list):
    """This function receives a list of time series and breaks, returns ordered FStats """
    import chowTest
    if(len(breaks)==0):return [-1,-1]
    Fstat_list=pd.DataFrame(columns=['break','FStat'])
    for i in range(len(breaks)):
        end_ind=breaks[i]
        x1=list(range(0, end_ind))
        x2=list(range(end_ind, len(values)))
        y1=values[:end_ind]
        y2=values[end_ind:]
        FStat=chowTest.f_value(y1,x1,y2,x2)[0]
        Fstat_list.loc[len(Fstat_list)] =[end_ind,FStat]
    Fstat_list=Fstat_list.sort_values(by=['FStat'],ascending=False)
    Fstat_list=Fstat_list.reset_index(drop=True)
    
    return Fstat_list
def timeSeriesL0Ingestion(l0data:Path)->nx.MultiDiGraph():
    #This function creates L0 for time series in graph to be processed as DFRE_KG
    G=nx.MultiDiGraph()
    df = pd.read_csv(l0data.resolve())
    print(len(df.columns)-1, "time series loaded")
    sampling_rate=int(df['ts'][1]-df['ts'][0])
    number_of_samples=len(df)
    if('ts' in list(df.columns)): 
        df=df.drop(columns=['ts'])
    df_cols=list(df.columns)
    for i in range(len(df_cols)):
        tsName="ts"+str(i+1) #shortname of the time series
        tsFullName=df_cols[i]       #full name of ts
        strucBreaks=''          #structural break
        origin=''                   #origin/device etc that ts belongs to
        event_names=''              #known events in the ts
        event_indicators=''         #known events' indicators' indices
        yang_module=""
        yang_keys=''
        category=''
        yang_leaves=''
        file_name=str(l0data.resolve())
        in_file_pointer=i+1
        G.add_node(tsName,tsFullName=tsFullName, sampling_rate=sampling_rate,file_name=file_name, in_file_pointer=in_file_pointer,strucBreaks=strucBreaks,category=category,origin=origin, event_names=event_names,
                   event_indicators=event_indicators,yang_module=yang_module,yang_keys=yang_keys,yang_leaves=yang_leaves,number_of_samples=number_of_samples)
    return G

def getSubConceptsFromContextKey(large_graph:nx.MultiDiGraph, hop_distance:int, keywords:Optional[list]=None, sql:Optional[str]=None)->nx.MultiDiGraph():
    """This function receives a KG, a list of keywords and hop distance. It returns composite ego graph.
    It can also be called through a sql string"""
    small_graph=nx.MultiDiGraph()
    if(keywords is not None):
        for key in keywords:
            small_graph=nx.compose(small_graph,nx.ego_graph(G=large_graph,n=key, radius=hop_distance))
    if(sql is not None):
        concepts=pd.DataFrame()
        relations=pd.DataFrame()
        relations=nx.convert_matrix.to_pandas_edgelist(large_graph)
        concepts =pd.DataFrame.from_dict(large_graph.nodes, orient='index')
        #by default concept names are indexes. resetting the index.
        concepts=concepts.rename_axis(["concepts"])
        concepts=concepts.reset_index()
        if(len(concepts)==0):
            concepts =pd.DataFrame.from_dict(large_graph.nodes)
            concepts.rename(columns={concepts.columns[0]:"concepts"},inplace=True)
        #run the query string
        result = pdsql.sqldf(sql, {**locals(), **globals()})
        for key in result["concepts"]:
             small_graph=nx.compose(small_graph,nx.ego_graph(G=large_graph,n=key, radius=hop_distance))
    #Construct context wrt the query result
    return small_graph













        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        