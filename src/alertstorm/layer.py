import networkx as nx

import dfre4net.knowledge as knowledge
from dfre4net.knowledge import KnowledgeGraph
from dfre4net.layer import L0, L1, L2

DFRE_SEVERITY_PROP = 'dfre_severity'
DFRE_SEMANTIC_PROP = 'dfre_semantic_severity'
DFRE_CATEGORY_PROP = 'dfre_category'

def derive_l1(l0: L0, l2: L2) -> L1:
    """
        Create an L1 representation combining the implicit context of the concepts of an
        L0 layer with the abstract knowledge of an L2 layer.

        For AlertStorm, L0 has context alerts and L2 has alert severity knowledge. The initial L1 is
        the set of all these alerts with an initial DFRESeverity equal to 0.
    """
    l0_g = l0.kg.g
    l1_g = l0_g.copy()
    """for node in l0_g.nodes: 
        l1_g.nodes[node][DFRE_SEVERITY_PROP] = 0.0
        l1_g.nodes[node][DFRE_SEMANTIC_PROP] = ''
        l1_g.nodes[node][DFRE_CATEGORY_PROP] = ''"""
    nx.set_node_attributes(l1_g, 'new', 'status')   # Set status to 'new' for these nodes
    nx.set_node_attributes(l1_g, 0.0, DFRE_SEVERITY_PROP)
    nx.set_node_attributes(l1_g, '', DFRE_SEMANTIC_PROP)
    nx.set_node_attributes(l1_g, '', DFRE_CATEGORY_PROP)

    #print("###AXT:: Layer::derive_l1(): l0 have {0} nodes, l1 have {1} nodes".format(len(l0_g.nodes), len(l1_g.nodes)))
    #print("###AXT:: Layer::derive_l1(): l0 have {0} nodes, l1 have {1} nodes".format(l0_g.nodes, l1_g.nodes))
    l1 = L1(KnowledgeGraph(l1_g))
    l1.intension = {}
    return l1

def create_new_l1() -> L1:
    """
        Create a new empty L1
    """

    l1 = L1(KnowledgeGraph())
    l1.intension = {}
    return l1

def merge_l1(l1_1: L1, l1_2: L1) -> L1:
    """
        Merge two L1 layer (i.e stm graph and intension)
    """

    l1 = L1(
            knowledge.merge(l1_1.stm, l1_2.stm)
        )
    l1.intension =  {**l1_1.intension, **l1_2.intension}
    return l1
