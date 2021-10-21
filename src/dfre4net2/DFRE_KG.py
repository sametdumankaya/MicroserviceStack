import networkx as nx
from typing import Optional, List
import logging
from pathlib import Path
from copy import copy, deepcopy
class DFRE_KG:
    def __init__(self, fname:Optional[Path]=None,graph: Optional[nx.MultiDiGraph]=None) -> None:
        if(fname is not None):
            #TODO: replace print with logging.info
            if("graphml" in str(fname)):
                print(f"Loading DFRE KG from {fname.resolve()}")
                self.g =nx.read_graphml(str(fname))
            elif('dfrescr' in str(fname)):
                self.g=self.load_KG_from_script(fname)
        elif(graph is not None):
            self.g = graph.copy()
        else:
            self.g=nx.MultiDiGraph()
    def load_KG_from_script(self,dfre_script_file:Path)  -> nx.MultiDiGraph():
        #load dfre kg from a dfre script
        #TODO: Full script processing must be implemented. Currently, only declarative statements are processed
        print(f"Loading DFRE KG from {dfre_script_file.resolve()}")
        local_g=nx.MultiDiGraph()
        with open(dfre_script_file.resolve()) as fp:
            Lines = fp.readlines()
            Lines=[x.strip() for x in Lines if x.strip()]
            for line in Lines: 
                ordered_nodes = [x.strip() for x in line.split('>>>')]
                if(len(ordered_nodes)==1):
                    local_g.add_node(ordered_nodes[0])
                else:
                    for i in range(len(ordered_nodes)-1):
                        if(not local_g.has_edge(ordered_nodes[i], ordered_nodes[i+1])):
                            local_g.add_edge(ordered_nodes[i], ordered_nodes[i+1])
        logging.info(len(local_g.nodes()), "nodes and", len(local_g.edges()), "edges are added to DFRE KG")
        return local_g
    def dump_KG_to_script(self,fname:str) -> None:
        #dump a kb to dfre script
        print(f"Dumping DFRE KG in {fname}")
        pass
    def dump_KG_to_graphml(self,fname:str) -> None:
        #dump a kb to graphml
        print(f"Dumping DFRE KG into {fname}")
        nx.write_graphml(self.g,fname)   
    def add_new_node_attrib(self,nodes:List,attrib_name:str,value:Optional[object]=None):
        #add a new attribute for nodes in the kb 
        if(value is None):
            for n in nodes:
                nx.set_node_attributes(self.g,{n:{attrib_name:''}})
        else:
            for n in nodes:
                nx.set_node_attributes(self.g,{n:{attrib_name:value}})
    def ingest_with_method(self,filepath:Path,method:object):
        #ingesting into kg by a method
        self.g=copy(method(filepath))
    def create_concept(self,concepts:tuple):
        #this method receives a container of (node, attribute dict) tuple to ingest.
        self.g.add_nodes_from(concepts)
    def create_relation(self,src_dest:list):
        self.g.add_edges_from(src_dest)
    def update_concept_value(self,concept_name:str,attribute_name:str,new_val:object):
        nx.set_node_attributes(self.g,{concept_name:{attribute_name:new_val}})
        
def merge_KG(*kgs: List[DFRE_KG]) -> DFRE_KG:
        """
            Merge a sequential list of Knowledge Graphs
        """
        print("merging", len(kgs), "DFRE KG's")
        if len(kgs) == 0: 
            return DFRE_KG()
        return DFRE_KG(None,nx.MultiDiGraph(nx.compose_all(map(lambda kg: kg.g, kgs))))