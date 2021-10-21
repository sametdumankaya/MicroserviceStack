import networkx as nx
from pathlib import Path
import os
import os,sys
sys.path.append(os.path.dirname(Path(os.path.abspath(__file__))))
import dfre4net2.layer as layer
from typing import Optional
import pandas as pd
from dfre4net2.DFRE_Agent import DFRE_Agent
from dfre4net2.task import Task, Priority
from dfre4net2.DFRE_KG import DFRE_KG
import uuid
import os
import dfre4net2.task
from timeseries import TimeSeriesEvents, TimeSeriesL1Analytics
import pickle
from dfre4net2.query_KG import sql_query_KG_concepts_pd
import timeseries.TimeSeriesL1Analytics
import timeseries.TimeSeriesEvents
import numpy as np
import ctypes
def createStructuralBreakAgent(t:Task):
    print("\n### STRUCTURAL BREAK ANALYSIS AGENT ###\n")
    aid=str(uuid.uuid4())#agent id
    l2fname="L2timeseriesStructuralBreak.dfrescr"
    DIR = Path(os.path.abspath(__file__)).parent
    l2fname = DIR / Path('./L2script/')/l2fname
    strucBreakFileName = DIR /'strucBreaks.csv'
    #Create strucBreak agent
    data=pickle.loads(t.data)
    print('Initializing a DFRE Agent as Structural Break Analysis Agent...')
    strucBreakAgent=DFRE_Agent(agent_id=aid,task=t,l2=layer.L2(longterm_kg=DFRE_KG(l2fname)),l0=layer.L0(shortterm_kg=DFRE_KG(graph=data)),
                               l1=layer.L1(shortterm_kg=DFRE_KG(graph=data)))
    print(len(data.nodes()), "timeseries received for analysis")
    strucBreaks=[]
    try:
        df_results=pd.read_csv(strucBreakFileName.resolve())
        for index, row in df_results.iterrows():
            if(row['strucBreaks'] is not np.nan):
                strucBreaks.append(row['strucBreaks'])
        print(f"Structural Break Analysis Agent: {len(df_results)} timeseries known...")
    except Exception as e:
        print(e)
        print("Structural Break Analysis Agent: No known previous structural breaks. Analyzing the new set...")
    sql="select * from concepts"
    df_l0_concepts=sql_query_KG_concepts_pd(strucBreakAgent.l0.kg,sql)
    #NaN value warnings are supressed
    np.seterr(all='ignore')
    df=pd.read_csv(df_l0_concepts['file_name'][0])
    if(len(strucBreaks)<1):
        df_results,strucBreaks=static_time_series_analysis(df,model='l1',min_val=3,jum_val=5,pen_val=3)
    #df_results.to_csv('strucBreaks.csv',index=False)
    ##INGEST ANALYSIS RESULTS INTO L2 & CREATE MAPPINGS
    print("Structural Break Analysis Agent: Ingesting results into L1...")
    concepts=list(data.nodes(data=True))
    for i in range(len(concepts)):
        
        try:
            concept_name=concepts[i][0]
            concept_full_name=concepts[i][1]['tsFullName']
            attribute_name='category'
            value=str(df_results[df_results['name']==concept_full_name][attribute_name].values[0])
            strucBreakAgent.l1._shortterm_knowledge.update_concept_value(concept_name, attribute_name, value)
        
            attribute_name='strucBreaks'
            value=df_results[df_results['name']==concept_full_name][attribute_name].values[0]
            strucBreakAgent.l1._shortterm_knowledge.update_concept_value(concept_name, attribute_name, value)
        except Exception as e:
            pass
    
    ##Ingestion L2 mappings
    concepts=list(strucBreakAgent.l1._shortterm_knowledge.g.nodes(data=True))
    print("Structural Break Analysis Agent: Updating L2 STM with new knowledge")
    for i in range(len(concepts)):
        concept_name=concepts[i][0]
        mapping_clue=concepts[i][1]['category']
        interlayer_mapping=strucBreakAgent.l2.map_intension(concept_name,mapping_clue)
         #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
        strucBreakAgent.l1.add_intension(interlayer_mapping)
        #generate extension map from intension
        strucBreakAgent.l2.add_extension(interlayer_mapping)
        #create and execute new task
    #cytoscape does not display lists []. cleaning list attrib for display purpose only
    outp=strucBreakAgent.generate_extension_map_network()
    # for node in list(outp.nodes(data=True)):
    #     name=node[0]
    #     sb=outp.nodes[name]
    #     if('strucBreaks' in sb.keys()): 
    #         sb=str(outp.nodes[name]['strucBreaks'])
    #         if(len(sb)>3):
    #             outp.nodes[name]['strucBreaks']=sb[1:-1]
    nx.write_graphml(outp,'structuralBreakAnalysisAgentL2Extension.graphml',prettyprint=True, infer_numeric_types=False)
    return t.task_id, strucBreakAgent.l1._shortterm_knowledge

def static_time_series_analysis(df:pd.DataFrame,model, min_val,jum_val,pen_val)->pd.DataFrame:
    df_results=pd.DataFrame(columns=['name','category','strucBreaks'])
    ####in live case, there will not be alignment value. delete this in live
    aligment_value=11111111
    df=TimeSeriesL1Analytics.cleanAlignmentValues(df,aligment_value)
    print("Normalizing time series...")
    #normalize time series. ZERO time series are extracted.
    df,zero_hor_cluster=TimeSeriesL1Analytics.normalizeTimeSeries(df)    
    #remove constant slopes from the df
    df,line_cluster=TimeSeriesL1Analytics.filter_lines(df)
    print(len(line_cluster.columns)+len(zero_hor_cluster.columns), "time series have constant slopes (lines)")
    #remove spikes
    df,spike_cluster=TimeSeriesL1Analytics.filter_spikes(df)
    #split squarewaves from spikes
    square_cluster, spike_cluster=TimeSeriesL1Analytics.splitSquaresFromSpikes(spike_cluster)
    print(len(spike_cluster.columns), "time series are spikes (only 0's and 1's)")
    print(len(square_cluster.columns), "time series are square signals")
    #Structural Breaks
    print('Analyzing structural breaks for',len(df.columns), "time series")
    strucBreaks=[]
    strucBreaks=TimeSeriesL1Analytics.get_strucBreaks_ruptures(df,model='l1',min_val=3,jum_val=5,pen_val=3)
    #Clean the last break which equals to len(df)
    for i in range(len(strucBreaks)):
        if(strucBreaks[i][-1]==int(len(df))):
            strucBreaks[i]=strucBreaks[i][:-1]
    #TODO: split limit estimation
    split_limit=int(len(df))/(jum_val+pen_val)
    df,no_break_cluster,strucBreaks=TimeSeriesL1Analytics.filter_no_structuralBreaks(df,strucBreaks,split_limit)
    print(len(no_break_cluster.columns),"time series have sampling error or no structures")
    #Chow test and line equation for structural breaks quality control
    strucBreaks=TimeSeriesL1Analytics.removeFPBreaks(df,strucBreaks,model='l1')
    #### construct results
    print('Analysis finished. Combining the results...')
    names=list(zero_hor_cluster.columns)
    for i in range(len(names)):
        new_row={'name':names[i],'category':'Constant Slopes','strucBreaks':''}
        df_results = df_results.append(new_row, ignore_index=True)
    
    names=list(line_cluster.columns)    
    for i in range(len(names)):
        new_row={'name':names[i],'category':'Constant Slopes','strucBreaks':''}
        df_results = df_results.append(new_row, ignore_index=True)
    
    names=list(spike_cluster.columns)    
    for i in range(len(names)):
        new_row={'name':names[i],'category':'Spikes','strucBreaks':''}
        df_results = df_results.append(new_row, ignore_index=True)
    
    names=list(square_cluster.columns)    
    for i in range(len(names)):
        new_row={'name':names[i],'category':'Square Waves','strucBreaks':''}
        df_results = df_results.append(new_row, ignore_index=True)
    
    names=list(no_break_cluster.columns)    
    for i in range(len(names)):
        new_row={'name':names[i],'category':'Time Series without Structural Breaks','strucBreaks':''}
        df_results = df_results.append(new_row, ignore_index=True)

    names=list(df.columns)    
    for i in range(len(names)):
        new_row={'name':names[i],'category':'Time Series with Structural Breaks','strucBreaks':strucBreaks[i]}
        df_results = df_results.append(new_row, ignore_index=True)
        
    return df_results,strucBreaks
if __name__ == "__main__":
    pass
