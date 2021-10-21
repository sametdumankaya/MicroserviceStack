from abc import ABC, abstractmethod
import networkx as nx
from typing import Union

from dfre4net.knowledge import KnowledgeGraph
from dfre4net.layer import AbstractionLayer, L0, L1, L2


def derive_l1(l0: L0, l2: L2) -> L1:
    """
        Create an L1 representation combining the implicit context of the concepts of an
        L0 layer with a long term knowledge (ontology), connecting.

        This automatically fills the extension of L2 object and the intension of the L1 object.
    """
    return L1(KnowledgeGraph(l0.kg.g))

class E2EInterLayerLinkBuilder:

    def __init__(self, source_endpoint: str, target_endpoint: str) -> None:
        self.source_endpoint = source_endpoint
        self.target_endpoint = target_endpoint
    
    def __extract_topology(self, kg: KnowledgeGraph) -> KnowledgeGraph:
        ## TODO: By now the kg is the topology itself
        return kg

    def build(self, l1: L1, l2: L2) -> None:
        """
            ## TODO: The information in L2 is not useful for this algorithm at the moment.
            #        It is hardcoded into the algorithm. L2 is only used to save its calculated extension.
            #        
        """
        topo_kg = self.__extract_topology(l1.kg)
        ## TODO: The cutoff of path calculation should be a parameter.
        paths = list(nx.all_shortest_paths(topo_kg.g, self.source_endpoint, self.target_endpoint))
        print(f"At least {len(paths)} paths between {self.source_endpoint} and {self.target_endpoint}")
        #paths = list(nx.all_simple_paths(topo_kg.g, self.source_endpoint, self.target_endpoint, cutoff=4))
        #networkx returns alternative node names with "(or)" which should be cleaned
        temp_paths=[]
        for path in paths:
            temp_p=[]
            for p in path:
                if("(or)" not in p):
                    temp_p.extend([p])
                else:
                    temp_p.extend([p.split(" (or) ")[0]])
            temp_paths.append(temp_p)
        paths=temp_paths
        l1_intension = {}
        l2_extension = {}
        #### Nodes
        # Source & Target
        l1_intension[self.source_endpoint] = 'SourceEndPoint'
        l2_extension['SourceEndPoint'] = self.source_endpoint
        l1_intension[self.target_endpoint] = 'TargetEndPoint'
        l2_extension['TargetEndPoint'] = self.target_endpoint
        # Inside paths
        l2_extension['Connection'] = connection_ext = []
        for path in paths:
            for node in path:
                if node != self.source_endpoint and node != self.target_endpoint:
                    l1_intension[node] = 'Connection'
                    connection_ext.append(node)
        #### Edges
        for path in map(nx.utils.pairwise, paths):
            for edge in path:
                e0, e1 = edge
                e0_intension, e1_intension = l1_intension[e0], l1_intension[e1]
                # Build Intension of L1
                l1_intension[(e0, e1)] = (e0_intension, e1_intension)
                if (not l1.kg.g.is_directed() and l2.ltm.g.is_directed()
                and (e1_intension, e0_intension) in l1.kg.g.edges):
                    ## L1 is undirected and L2 is directed
                    ## If the mapping into L2 exists
                    ## Put the back edge manually into L1 intension.
                    l1_intension[(e1, e0)] = (e1_intension, e0_intension)
                # Build Extension of L2
                if (e0_intension, e1_intension) in l2.ltm.g.edges:
                    if (e0_intension, e1_intension) not in l2_extension:
                        l2_extension[(e0_intension, e1_intension)] = []
                    l2_extension[(e0_intension, e1_intension)].append((e0, e1))
                    if (not l2.ltm.g.is_directed() and l1.kg.g.is_directed()
                    and e0_intension != e1_intension
                    and (e1, e0) in l1.kg.g.edges):
                        ## L2 is undirected and L1 is directed
                        ## If the edge is not a self loop and the back edge mapping into L1 exists
                        ## Put this back edge manually into L2 extension.
                        if (e1_intension, e0_intension) not in l2_extension:
                            l2_extension[(e1_intension, e0_intension)] = []
                        l2_extension[(e1_intension, e0_intension)].append((e1, e0))
                
        l1.intension = l1_intension
        l2.extension = l2_extension
