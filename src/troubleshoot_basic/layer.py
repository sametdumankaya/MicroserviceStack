from abc import ABC, abstractmethod
import networkx as nx
from typing import List, Tuple, Union

class Layer:
    def __init__(self, layer_graph: nx.DiGraph) -> None:
        self.graph = layer_graph

class L0(Layer):
    
    def __init__(self, 
                l0_concepts: List[str], 
                l0_relations: List[Union[Tuple[str, str],Tuple[str, str, str]]],
                l0_concepts_tags: dict) -> None:
        g = nx.DiGraph()
        g.add_nodes_from(l0_concepts)
        g.add_edges_from(l0_relations)
        super().__init__(g)
        self.tag_dict = l0_concepts_tags

class LayerLoader(ABC):
    """ Abstract class for creating concept layers. """
    @abstractmethod
    def create(self) -> Layer:
        raise NotImplementedError

def generate_l1(l0: L0, ontology: nx.MultiDiGraph) -> nx.DiGraph:
    l1 = nx.DiGraph()
    ## Add L0 concepts that have an associated abstraction in L2
    for l0_node, l2_concept in l0.tag_dict.items():
        if l2_concept not in ontology.nodes: continue
        l2_description = ontology.nodes[l2_concept]
        l1.add_node(l0_node, **l2_description)
    ## Cast L0 edges into L1 semantic relations according to relations known in L2
    for l0_node1, l0_node2, l0_edge_data in l0.graph.edges(data=True):
        if l0_node1 in l1.nodes and l0_node2 in l1.nodes: # Look only at L0 nodes mapped into L2
            l2_edges = list(
                filter(lambda e: e[0] == l0.tag_dict[l0_node1] and e[1] == l0.tag_dict[l0_node2], 
                ontology.edges(keys=True))
            )
            if 'relation' in l0_edge_data:
                ## L0 is specifying the relation, use it.
                l0_rel = l0_edge_data['relation']
                l2_understands = any(map(lambda e: e[2] == l0_rel, l2_edges))
                if not l2_understands:
                    ## Issue warning that L2 does not understand this relation.
                    print(f"WARNING: L0 edge ({l0_node1}, {l0_node2}) is well defined for L1 generation with relation"+\
                        f"{l0_rel} are no relations on mapped L2 abstractions.")
                    print("Mapping of L0 concepts:")
                    print(f"L2({l0_node1}) ==> {l0.tag_dict[l0_node1]}")
                    print(f"L2({l0_node2}) ==> {l0.tag_dict[l0_node2]}")
                l1.add_edge(l0_node1, l0_node2, relation=l0_rel)
            elif len(l2_edges) == 0:
                ## L0 provides no relation for the nodes and neither does L2
                print(f"WARNING: L0 edge ({l0_node1}, {l0_node2}) provides no description and found no L2 layer relation.")
                print("Mapping of L0 concepts:")
                print(f"L2({l0_node1}) ==> {l0.tag_dict[l0_node1]}")
                print(f"L2({l0_node2}) ==> {l0.tag_dict[l0_node2]}")
            elif len(l2_edges) == 1:
                ## L0 provides no relation for the nodes but L2 does.
                l1.add_edge(l0_node1, l0_node2, relation=l2_edges[0][2])
            else:
                ## L0 provides no relation for the nodes and L2 has ambiguous relations.
                ## TODO: Better handle this situation?
                print(f"WARNING: Multiple L2 relations for L0 edge ({l0_node1}, {l0_node2}). Ambiguous ontology?")
                print(f"L0 relation has no further info. Possible L2 relations are: {list(e[3] for e in l2_edges)}")
                print("Mapping of the L0 concepts:")
                print(f"L2({l0_node1}) ==> {l0.tag_dict[l0_node1]}")
                print(f"L2({l0_node2}) ==> {l0.tag_dict[l0_node2]}")
    return l1

class Lstar(Layer):

    L2_WORKING = 'L2w'
    L2_BROKEN = 'L2b'

    def __init__(self, users: List[str]=[]) -> None:
        self.users = users
        g = nx.DiGraph()
        g.add_nodes_from([
            'stability',
            'instability',
            Lstar.L2_WORKING,
            Lstar.L2_BROKEN,
            *users
        ])
        for user in users:
            g.add_edge(user, 'stability', relation='wants')
            g.add_edge(user, 'instability', relation='not_wants')
        g.add_edge(Lstar.L2_WORKING, 'stability', relation='causes')
        g.add_edge(Lstar.L2_BROKEN, 'instability', relation='causes')
        super().__init__(g)
        self.state = Lstar.L2_WORKING
