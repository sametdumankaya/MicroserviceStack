import pandas as pd
import networkx as nx
from typing import Optional
from problog.program import PrologString
from problog.core import ProbLog
from problog import get_evaluatable
import numpy as np
_=np.seterr(all='ignore')
def getYangElementsFromFeature(title:str,i:int):
    """This function receives a title of a time series in Wadget format, 
    extracts and returns module name, leaf name and key values"""
    if(len(title)==0):
        print("empty title")
        return
    module_name=""
    key_values=[]
    leaf_name=""
    temp_list=title.split("[")
    module_name=temp_list[0]
    temp_list=temp_list[1].split("]")
    leaf_name=temp_list[1]
    #There is an error in the naming convention of Wadget. Fixing it
    if(len(leaf_name)<1):leaf_name="unknown"+str(i)
    if(leaf_name[0]=='-'): leaf_name=leaf_name[1:]

    if(len(temp_list[0])==0):
        key_values=['unknown'+str(i),'unknown'+str(i)]
    elif("address:prefix-length:" in temp_list[0]):
        add_list=temp_list[0].split("address:prefix-length:")
        l1=["address-prefix-length"]
        l1.extend(add_list[1].split(":"))
        l1= ["unknown"+str(i) if len(x)==0 else x for x in l1]
        l3=['address']
        l2=(add_list[0].split(":address:")[0]).split(":")
        l4=[(add_list[0].split(":address:")[1]).replace(":",".")]
        l2.extend(l3)
        l2.extend(l4)
        l2.extend(l1)
    elif(temp_list[0].count("destination-address:")>1):
        add_list=temp_list[0].split("destination-address:")
        l1=add_list[0].split(":")
        l1=[x for x in l1 if len(x)>0]
        l2=['destination-address']
        l2.extend([add_list[1].replace(":",".")])
        l3=add_list[2].split(":")
        l1.extend(l2)
        l1.extend(l3)
        key_values=l1      
    else:
        key_values=temp_list[0].split(":")

    return module_name, key_values,leaf_name

def constructGraphFromYangColNames(df:pd.DataFrame,fname:Optional[str]=None,):
    """This function receives a dataframe of time series whose names based on Yang Models.
    Constructs and returns a graph after saves it to graphml"""
    G=nx.MultiDiGraph()
    col_names=list(df.iloc[:,1])
    node_names=list(df.iloc[:,0])
    for i in range(len(col_names)):
        title=col_names[i].encode().decode()
        node=node_names[i]
        module_name,key_values,leaf_name=getYangElementsFromFeature(title,i)
        G.add_node(str(module_name), yang_type="module",origin="yangModelAnalysis")
        G.add_node(str(leaf_name), yang_type="leaf",origin="yangModelAnalysis")
        G.add_edge(str(node),str(leaf_name),relation="leaf",keys=','.join([str(x) for x in key_values]))
        G.add_edge(str(node),str(module_name),relation="module",keys=','.join([str(x) for x in key_values]),module=module_name)
        for i in range(0,len(key_values),2):
            key_var=key_values[i]
            try:
                key_name=key_values[i+1]
            except Exception as e:
                pass
            G.add_node(key_name,yang_type="key",origin="yangModelAnalysis")
            G.add_edge(str(node),str(key_name),relation=str(key_var))
    if(fname is not None):
        nx.write_graphml(G,fname,encoding='utf-8', prettyprint=True, infer_numeric_types=False)
    print("done")
    return G

def getHistogramFromDf(dfObj:pd.DataFrame,ts_len:int):
    """This function receives a dataframe of structural breaks and flattens it (macro scale)"""
    histogram_cnt=[]
    counts = pd.value_counts(dfObj.values.flatten())
    for i in range(ts_len):
        if(counts.get(i)!=None):
            histogram_cnt.append(counts.get(i))
        else:
            histogram_cnt.append(0)
    return histogram_cnt

def analyzeHistogramForEvents(df_l1_concepts:pd.DataFrame):
    number_of_samples=int(df_l1_concepts['number_of_samples'][0:1].values)
    sampling_rate=int(df_l1_concepts['sampling_rate'][0:1].values)
    df_l1_concepts=pd.DataFrame(df_l1_concepts['strucBreaks'])
    strucBreaks=[]
    for index, rows in df_l1_concepts.iterrows():
        data=(rows.values[0])[1:-1]
        data= [int(i) for i in data.split(',')]
        strucBreaks.append(data)
    dfObj=pd.DataFrame(strucBreaks)
    histogram_cnt=getHistogramFromDf(dfObj,number_of_samples)
    ts_freq_threshold=20
    peek_ratio=0.3
    events= getCandidateEvents(histogram_cnt,number_of_samples, ts_freq_threshold, peek_ratio, sampling_rate)
    events.index.name='Event Number'
    events.index +=1
    return strucBreaks,histogram_cnt, events

def getCandidateEvents(histogram_cnt:list,ts_len:int, ts_freq_threshold:int, peek_ratio:float, sampling_rate:int):
    """This function analysis the histogram of structural breaks and creates a dataframe of events"""
    import numpy as np
    from scipy.signal import find_peaks
    from heapq import nsmallest
    import pandas as pd
    column_names=["leading indicator","main indicator","trailing indicator"]
    events=pd.DataFrame(columns=column_names)
    #Candidates above the threshold
    filter_cnt=[]
    for cnt in histogram_cnt:
        if(cnt>ts_freq_threshold):
            filter_cnt.append(int(cnt))
        else:
            filter_cnt.append(0)
    x=np.array(filter_cnt)
    peax, _ = find_peaks(x, height=np.max(filter_cnt)*peek_ratio)
    
    #merge immediately conseq peaks
    peaks=[]
    for p in range(0,len(peax)-1):
        if(np.max(filter_cnt[peax[p]+1:peax[p+1]])==0):
            peaks.append(filter_cnt.index(min(filter_cnt[peax[p]],filter_cnt[peax[p+1]]),peax[p]))
    peaks = [x for x in peax if x not in peaks]
    tmp=[]
    for p in range(0,len(peaks)-1):
        if(abs(peaks[p]-peaks[p+1])<=2):
            tmp.append(filter_cnt.index(min(filter_cnt[peaks[p]],filter_cnt[peaks[p+1]]),peaks[p]))
    peaks = [x for x in peaks if x not in tmp]

    
    
    for i in range(len(peaks)):
        if(i==0):
            leading_indicator=histogram_cnt.index(np.max(histogram_cnt[0:peaks[0]]))
        else:
            leading_indicator=filter_cnt.index(np.max(filter_cnt[peaks[i-1]+1:peaks[i]-1]),peaks[i-1]+1)
        main_indicator=peaks[i]
        s_int=main_indicator+1
        if(i==len(peaks)-1):
            e_int=ts_len
        else:
            e_int=peaks[i+1]-1
        trailing_space=nsmallest(2, np.unique(filter_cnt[s_int:e_int]))[-1]
        trailing_indicator=filter_cnt.index(trailing_space,s_int)
        events.loc[len(events)]=[leading_indicator,main_indicator,trailing_indicator]
    return events
def guessTopologyFromKeys(ts_names:list, keyword:str)->nx.Graph():
    """This function receives a string list of time series names and constructs a graph using the yang models"""
    G=nx.Graph()
    #Root
    G.add_node(keyword)
    nx.set_node_attributes(G, '', 'location')
    for t in ts_names:
        m,keys,l=getYangElementsFromFeature(t,int(ts_names.index(t)))
        if(len(keys)>1):
            if("neighbor-address" in keys): #address
                ind=keys.index("neighbor-address")+1
                if(len(keys[ind].split(".")[0])<4):                
                    G.add_node(keys[ind],category="ipv4")
                else:
                    G.add_node(keys[ind],category="ipv6")
            if("node-name" in keys):
                ind=keys.index("node-name")+1
                G.add_edge("node-name", keys[ind])
            if("address" in keys):
                ind=keys.index("address")+1
                if(len(keys[ind].split(".")[0])<4):                
                    G.add_node(keys[ind],category="ipv4")
                else:
                    G.add_node(keys[ind],category="ipv6")
            if(keyword in keys): #interface
                ind=keys.index(keyword)+1
                G.add_edge(keyword,keys[ind])
            if("interface-name" in keys[0]):
                if(len(keys)==2):
                   G.add_edge(keyword,keys[1]) 
                elif(len(keys)==4):
                   G.add_edge(keys[1],keys[3],relation='location')
                else:
                   G.add_edge(keys[1],keys[5],relation='location')
                   if(len(keys[3].split(".")[0])<4):                
                       G.add_edge(keys[1], keys[3],category="ipv4")
                   else:
                       G.add_edge(keys[1], keys[3],category="ipv6")                    
    return G

def getProblogResultFromNx(graphs:list,queryconcept:str)->nx.MultiDiGraph:
    p = PrologString("""
    0.3::stress(X) :- person(X).
    0.2::influences(X,Y) :- person(X), person(Y).
    smokes(X) :- stress(X).
    smokes(X) :- friend(X,Y), influences(Y,X), smokes(Y).
    0.4::asthma(X) :- smokes(X).
    person(angelika).
    person(joris).
    person(jonas).
    person(dimitar).
    
    friend(joris,jonas).
    friend(joris,angelika).
    friend(joris,dimitar).
    friend(angelika,jonas).
    query(smokes(_)).
    """)
    get_evaluatable().create_from(p).evaluate()
        
def nx2problog(small_graph:nx.MultiDiGraph,query_concept:Optional[str]=None)->str:
    query_str=""
    for (u,v,c) in small_graph.edges(data=True):
        if('relation' in c):
            query_str=query_str+c['relation']+"("+u+","+v+").\n"
    for node in small_graph.nodes(data=True):
        pass

    """0.10::classified_event(X):- ecmp_imbalance(X).
    0.10::classified_event(X):- buffer_starvation(X).
    
    
    0.60::ecmp_imbalance(X):-has(X,Y),key(Y),ipv6(Y),has(X,Z),leaf(Z), memory(Z),module(W),address_family(W).
    ecmp_imbalance(X):-has(X,Y),key(Y),ipv6(Y),has(X,Z),leaf(Z), memory(Z),module(W),address_family(W).
    
    buffer_starvation(X):-has(X,Y),key(Y),ipv6(Y),has(X,Z),leaf(Z), mib_counter(Z), module(W),traffic(W).
    
    0.40::has(event1,ipv6-unicast).
    0.40::key(ipv6-unicast).
    0:40::ipv6(ipv6-unicast).
    has(event1,global_paths_memory).
    leaf(global_paths_memory).
    memory(global_paths_memory).
    has(event1,af_process_nome).
    module(af_process_nome).
    address_family(af_process_nome).
    mib_counter(data).
    query(classified_event(_))."""
        
        
        
        
        
        
        
        
        
        