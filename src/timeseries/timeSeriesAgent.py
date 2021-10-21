import networkx as nx
import argparse
from pathlib import Path
import os,sys
sys.path.append(os.path.dirname(Path(os.path.abspath(__file__))))
import dfre4net2.layer as layer
from typing import Optional,List
import pandas as pd
from dfre4net2.DFRE_Agent import DFRE_Agent
from dfre4net2.task import Task, Priority
from dfre4net2.DFRE_KG import DFRE_KG
import uuid
import os
import dfre4net2.task
from timeseries import TimeSeriesEvents, TimeSeriesL1Analytics, structuralBreakAnalysisAgent, yangModelAgent
import pickle
import redis
from dfre4net2.query_KG import sql_query_KG_concepts_pd,sql_query_KG_relations_pd,cleanGraphSymbols
import ctypes
USE_CASE_ID='timeseries'
def get_cli_parser() -> argparse.ArgumentParser:
    cli_parser = argparse.ArgumentParser(
        prog=sys.argv[0]+' '+USE_CASE_ID,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )
    ## Help
    cli_parser.add_argument(
        '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='Start time series use-case.'
    )
    ## fname parameter
    cli_parser.add_argument(
        '--fname',
        type=str,
        default='merged_191015_1949.csv',
        help='csv file name containing time series. Each column is a time series starting with a name.'
    )
    ## cytoscape parameter
    cli_parser.add_argument(
        '--enableCytoscape',
        default=False,
        help='Enable ctyoscape visualization. Make sure cytoscape is running.',
        action='store_true',
        dest='enableCytoscape'
    )
    ## fname parameter
    cli_parser.add_argument(
        '--redishost',
        type=str,
        default='localhost',
        help='Host address for redis.'
    )
    ## fname parameter
    cli_parser.add_argument(
        '--redisport',
        type=int,
        default=6379,
        help='Port number for redis'
    )
    
    return cli_parser




class TimeSeriesAgent(DFRE_Agent):
    def __init__(self,agent_id:Optional[str]=None,l2ltm_file:Optional[Path]=None,l0data:Optional[object]=None,l0ingestionmethod:Optional[object]=None,enableCytoscape:Optional[bool]=None,description:Optional[str]=None) -> None:
        if(l2ltm_file is None and agent_id is None):
            super().__init__(enableCytoscape=enableCytoscape,description=description)
        else:
            super().__init__(agent_id=agent_id,l2=layer.L2(longterm_kg=DFRE_KG(l2ltm_file)),enableCytoscape=enableCytoscape,description=description)
        if(l0data is not None and l0ingestionmethod is not None):
            g=l0ingestionmethod(l0data)
            self.l0=layer.L0(shortterm_kg=DFRE_KG(graph=g))
            self.l1=layer.L1(shortterm_kg=DFRE_KG(graph=g))
    
    def detect_events(self):
        print("Time Series Agent: Detecting events based on structural break analysis across time series...")
        sql="select * from concepts where strucBreaks <> \'\'"
        df_l1_concepts=sql_query_KG_concepts_pd(self.l1.kg,sql)
        print(len(df_l1_concepts))
        strucBreaks,histogram_cnt, events= TimeSeriesEvents.analyzeHistogramForEvents(df_l1_concepts)
        print("Time Series Agent: Attempting to displaying event histogram...")
        TimeSeriesL1Analytics.plotEventHistograms(histogram_cnt,int(df_l1_concepts['number_of_samples'][0:1].values),events)
        print("Time Series Agent: Displaying summary of events...\n")
        print(events)
        print("Time Series Agent: Ingesting ",len(events)," events in L2...")
        for i in range(len(events)):
            #Ingest Unclassified Events 
            concept_name='Event'+ str(i+1)
            leading_indicator=events['leading indicator'].iloc[i]
            main_indicator=events['main indicator'].iloc[i]
            trailing_indicator=events['trailing indicator'].iloc[i]
            concept=(concept_name,{'leading indicator':leading_indicator,'main indicator':main_indicator,'trailing indicator':trailing_indicator,'category':''})
            self.ingestL2([concept])
            self.l2._shortterm_knowledge.create_relation([('Unclassified Events',concept_name)])
            #Ingest Event histogram under Temporal Grouping
            concept_name=str(i+1)+ '. Event Histogram' 
            concept=(concept_name,{'leading indicator':leading_indicator,'main indicator':main_indicator,'trailing indicator':trailing_indicator})
            self.ingestL2([concept])
            self.l2._shortterm_knowledge.create_relation([('Temporal Grouping',concept_name)])
            ts_leading_list=[]
            ts_main_list=[]
            ts_trailing_list=[]
            for j in range(len(strucBreaks)):
                if(leading_indicator in strucBreaks[j]):
                    l1_concept_name=df_l1_concepts['concepts'][j]
                    ts_leading_list.append(l1_concept_name)
                if(main_indicator in strucBreaks[j]):
                    l1_concept_name=df_l1_concepts['concepts'][j]
                    ts_main_list.append(l1_concept_name)
                if(trailing_indicator in strucBreaks[j]):
                    l1_concept_name=df_l1_concepts['concepts'][j]
                    ts_trailing_list.append(l1_concept_name)            
            sub_concept=str(i+1)+ '. Leading Indicator' 
            self.l2._shortterm_knowledge.create_relation([(concept_name,sub_concept)])
            concept=(sub_concept,{'structural break timestamp':leading_indicator,'number of time series':len(ts_leading_list)})
            self.ingestL2([concept])
            #construct interlayer mapping between L2 indicators and L1 concepts
            for l1_concept in ts_leading_list:
                interlayer_mapping=self.l2.map_intension(l1_concept,sub_concept)
                #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
                self.l1.add_intension(interlayer_mapping)
                #generate extension map from intension
                self.l2.add_extension(interlayer_mapping)
            sub_concept=str(i+1)+ '. Main Indicator' 
            self.l2._shortterm_knowledge.create_relation([(concept_name,sub_concept)])
            concept=(sub_concept,{'structural break timestamp':main_indicator,'number of time series':len(ts_main_list)})
            self.ingestL2([concept])
            #construct interlayer mapping between L2 indicators and L1 concepts
            for l1_concept in ts_main_list:
                interlayer_mapping=self.l2.map_intension(l1_concept,sub_concept)
                #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
                self.l1.add_intension(interlayer_mapping)
                #generate extension map from intension
                self.l2.add_extension(interlayer_mapping)
            sub_concept=str(i+1)+ '. Trailing Indicator' 
            self.l2._shortterm_knowledge.create_relation([(concept_name,sub_concept)])
            concept=(sub_concept,{'structural break timestamp':trailing_indicator,'number of time series':len(ts_trailing_list)})
            self.ingestL2([concept])
            #construct interlayer mapping between L2 indicators and L1 concepts
            for l1_concept in ts_trailing_list:
                interlayer_mapping=self.l2.map_intension(l1_concept,sub_concept)
                #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
                self.l1.add_intension(interlayer_mapping)
                #generate extension map from intension
                self.l2.add_extension(interlayer_mapping)
    def push_task_for_self(self,function_name:str):
        tid=str(uuid.uuid4())#task id
        process=self.self_task_received
        data=tid
        data=pickle.dumps(data)
        t=Task(description='Inform Task Manager about Yang Model Analysis on a shared DFRE KG',task_id=str(tid),requester_agent_id=self.agent_id,priority=Priority.MID,data=data,process=process)
        r_response=r.rpush("Task Manager", pickle.dumps(t))
        if(r_response!=0): print("Time Series Agent: Informed Task Manager about co-working on the DFRE KG with another DFRE Agent. Waiting for the results...")
        isTaskForSelfGranted=r.get(self.agent_id)
        while isTaskForSelfGranted is None:
            isTaskForSelfGranted=r.get(self.agent_id)
        isTaskForSelfGranted=pickle.loads(isTaskForSelfGranted)
        if(isTaskForSelfGranted):
            print("Time Series Agent: Permission granted. Initiating another DFRE Agent for cooperation...")
            method_to_call = getattr(self, function_name)
            method_to_call()

    
    
    def request_yang_model_analysis_by_reference(self):
        tid=str(uuid.uuid4())#task id
        l1reference=pickle.dumps(id(self.l1.kg.g))
        process=yangModelAgent.yangModelAgentByReference
        t=Task(description='Yang Model Analysis',task_id=str(tid),requester_agent_id=self.agent_id,priority=Priority.MID,data=l1reference,process=process)
        tid,isDone=yangModelAgent.yangModelAgentByReference(t)
        if(isDone):
            print("\n### TIME SERIES AGENT ###\n")
            print("Time Series Agent: Yang Model Analysis Agent finished working. Updating L2 STM with new knowledge...") 
            concepts=list(self.l1.kg.g.nodes(data=True))    
            for i in range(len(concepts)):
               concept_name=concepts[i][0]
               mapping_clue=None
               if('yang_type' in concepts[i][1]): 
                   mapping_clue=concepts[i][1]['yang_type']
               if(mapping_clue is not None):
                    if(len(mapping_clue)>0):
                        interlayer_mapping=self.l2.map_intension(concept_name,mapping_clue)
                         #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
                        self.l1.add_intension(interlayer_mapping)
                        #generate extension map from intension
                        self.l2.add_extension(interlayer_mapping)
    
    def classify_events(self,UnclassifiedEventName:str,expertiseFile:Path):
    #load event expertise
        pass    


    def self_task_received(self,data:Optional[object]=None):
        isTaskForSelfGranted=True
        return data, isTaskForSelfGranted
    
def main(args: List[str]):
    cli_parser = get_cli_parser()
    cli_options = cli_parser.parse_args(args)
    global r
    r = redis.Redis(host=cli_options.redishost,port=cli_options.redisport, db=0)
    print("\n### TIME SERIES AGENT ###\n")
    ##initialize agent ID and L0 and L2 data location
    aid=str(uuid.uuid4())#agent id
    l2fname="L2timeseries.dfrescr"
    DIR = Path(os.path.abspath('__file__')).parent
    l2fname = DIR / Path('./timeseries/L2script')/l2fname
    l0fname=cli_options.fname
    l0fname = DIR / Path('./timeseries/')/l0fname
    #Create timeSeriesAgent  agent
    print('Initializing a DFRE Agent as Time Series Agent...')
    enableCytoscape=cli_options.enableCytoscape
    timeSeriesAgent=TimeSeriesAgent(agent_id=aid,l2ltm_file=l2fname,l0data=l0fname,l0ingestionmethod=TimeSeriesL1Analytics.timeSeriesL0Ingestion,enableCytoscape=enableCytoscape, description="Time Series Agent")
    if(enableCytoscape):
        print("Time Series Agent: Sending current DFRE KG to Cytoscape...")
        timeSeriesAgent.send2Cytoscape()
    #create a task for structural break
    tid=str(uuid.uuid4())#task id
    data=pickle.dumps(timeSeriesAgent.l0.kg.g)
    process=structuralBreakAnalysisAgent
    t=Task(description='Structural Break Analysis',task_id=str(tid),requester_agent_id=aid,priority=Priority.HIGH,data=data,process=process.createStructuralBreakAgent)
    r_response=r.rpush("Task Manager", pickle.dumps(t))
    if(r_response!=0): print("Time Series Agent: New task sent to Task Manager. Waiting for the resulting DFRE KG...")
    result_KG=r.get(timeSeriesAgent.agent_id)
    #wait for thre result
    while result_KG is None:
       result_KG=r.get(timeSeriesAgent.agent_id)
    result_KG=pickle.loads(result_KG)
    ##Ingest the result
    print('Time Series Agent:',t.description, "results received. Ingesting in L1...")
    timeSeriesAgent.l1._shortterm_knowledge=result_KG
    print("Time Series Agent: Updating L2 STM with new knowledge")
    concepts=list(timeSeriesAgent.l1._shortterm_knowledge.g.nodes(data=True))
    for i in range(len(concepts)):
        concept_name=concepts[i][0]
        mapping_clue=concepts[i][1]['category']
        interlayer_mapping=timeSeriesAgent.l2.map_intension(concept_name,mapping_clue)
         #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
        timeSeriesAgent.l1.add_intension(interlayer_mapping)
        #generate extension map from intension
        timeSeriesAgent.l2.add_extension(interlayer_mapping)
    if(enableCytoscape):
        print("Time Series Agent: Sending current DFRE KG to Cytoscape...")
        timeSeriesAgent.send2Cytoscape()
    ###EVENT ANALYSIS
    print("Time Series Agent: Detecting events...")
    timeSeriesAgent.detect_events()
    l2fname='L2yangModels.dfrescr'
    DIR = Path(os.path.abspath('__file__')).parent
    l2fname = DIR / Path('./timeseries/L2script')/l2fname
    x=DFRE_KG()
    graph_expertise=x.load_KG_from_script(dfre_script_file=l2fname)
    timeSeriesAgent.l2.stm.create_relation(list(graph_expertise.edges()))
    timeSeriesAgent.push_task_for_self('request_yang_model_analysis_by_reference')
    if(enableCytoscape):
        print("Time Series Agent: Sending current DFRE KG to Cytoscape...")
        timeSeriesAgent.send2Cytoscape()
    print("Time Series Agent: Ingesting expertise on classified events in L2")    
    l2fname='L2fromDrew.dfrescr'
    DIR = Path(os.path.abspath('__file__')).parent
    l2fname = DIR / Path('./timeseries/L2script')/l2fname
    x=DFRE_KG()
    graph_expertise=x.load_KG_from_script(dfre_script_file=l2fname)
    timeSeriesAgent.l2.stm.create_relation(list(graph_expertise.edges()))
    #unclassifiedEventName='Event1'
    #timeSeriesAgent.classify_events(unclassifiedEventName)
        
    ###START:write final extension into graphml
    outp=timeSeriesAgent.generate_extension_map_network()
    outp=cleanGraphSymbols(outp)
    nx.write_graphml(outp, "timeSeriesAgentL2Extension.graphml",prettyprint=True, infer_numeric_types=False)
    return

if __name__ == "__main__":
    main(sys.argv[1:])

    















    #x=pickle.loads(r.lpop("Task Manager"))
    #print(x.description)
    #x=pickle.loads(r.lpop("Task Manager"))
    #print(x.description)
    



# tsAgent.l1.kg.dump_KG_to_graphml("timeseriesL0.graphml")
# tsAgent.l2.ltm.dump_KG_to_graphml("timeseriesL2.graphml")
# graph=timeSeriesL0Ingestion(l0fname)
# a=DFRE_KG(graph=graph)
# r.rpush("Task Manager", pickle.dumps(y))








