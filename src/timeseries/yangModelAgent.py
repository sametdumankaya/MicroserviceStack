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
from timeseries import TimeSeriesEvents
import pickle
from dfre4net2.query_KG import sql_query_KG_concepts_pd
import timeseries.TimeSeriesL1Analytics
import timeseries.TimeSeriesEvents
import numpy as np
import ctypes

def yangModelAgent(t:Task):
    pass

def yangModelAgentByReference(t:Task)->bool:
    print("\n### YANG MODEL AGENT ###\n")
    isDone=False
    #CREATE AGENT
    aid=str(uuid.uuid4())#agent id
    l2fname="L2yangModels.dfrescr"
    DIR = Path(os.path.abspath('__file__')).parent
    #YANG MODEL L2
    l2fname = DIR / Path('./timeseries/L2script/') /l2fname
    print('Initializing a DFRE Agent as Yang Model Agent without L1...')
    print('Yang Model Agent: Using a reference to requester agent\'s L1...')
    #GET THE REFERENCE TO THE GRAPH
    reference=pickle.loads(t.data)
    #CAST IT BACK TO GRAPH
    referenced_graph=ctypes.cast(reference,ctypes.py_object).value
    #CREATE THE YANG MODEL AGENT
    yangModelAgent=DFRE_Agent(agent_id=aid,task=t,l2=layer.L2(longterm_kg=DFRE_KG(l2fname)),l0=layer.L0(),l1=layer.L1())
    yangModelAgent.l0.kg.g=referenced_graph
    yangModelAgent.l1.kg.g=referenced_graph
    sql="select concepts,tsFullName from concepts"
    df_l1_concepts=sql_query_KG_concepts_pd(yangModelAgent.l1.kg,sql)
    print('Yang Model Agent: Constructing knowledge graph from data names...')
    G=TimeSeriesEvents.constructGraphFromYangColNames(df_l1_concepts,"yangModelFromTimeSeries.graphml")
    print('Yang Model Agent: Ingesting results in L1...')
    referenced_graph.add_nodes_from(G.nodes(data=True))
    referenced_graph.add_edges_from(G.edges(data=True))
    yangModelAgent.l1._shortterm_knowledge.g=referenced_graph
    print('Yang Model Agent: Updating L2 STM with new knowledge...')
    concepts=list(yangModelAgent.l1._shortterm_knowledge.g.nodes(data=True))    
    for i in range(len(concepts)):
        concept_name=concepts[i][0]
        mapping_clue=None
        if('yang_type' in concepts[i][1]): 
            mapping_clue=concepts[i][1]['yang_type']
        if(mapping_clue is not None):
            if(len(mapping_clue)>0):
                interlayer_mapping=yangModelAgent.l2.map_intension(concept_name,mapping_clue)
                 #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
                yangModelAgent.l1.add_intension(interlayer_mapping)
                #generate extension map from intension
                yangModelAgent.l2.add_extension(interlayer_mapping)
    isDone=True
    nx.write_graphml(yangModelAgent.generate_extension_map_network(),'yangModelAgentL2Extension.graphml')
    return t.task_id,isDone

if __name__ == "__main__":
    pass



# G=nx.Graph()
# H=nx.Graph()

# G.add_node(1,name='test',data=2)
# G.add_node(2,life='test')
# G.add_node(3)
# H.add_node(1,name='hh',love=2)
# H.add_node(2)
# H.add_node(4)
# #MERGES ATTRIBUTES. if both have same attrib names, preserves the value of the left one left 
# F=nx.compose(H,G)