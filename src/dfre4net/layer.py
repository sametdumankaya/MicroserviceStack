from abc import ABC, abstractmethod
from functools import partial
from itertools import starmap
import networkx as nx
from typing import Optional, Union

from .knowledge import KnowledgeGraph

class AbstractionLayer(ABC):

    def __init__(self) -> None:
        self._longterm_knowledge = KnowledgeGraph()
        self._shortterm_knowledge = KnowledgeGraph()
    @property
    def ltm(self) -> KnowledgeGraph:
        return self._longterm_knowledge
    @property
    def stm(self) -> KnowledgeGraph:
        return self._shortterm_knowledge
    def __repr__(self):
        return "BaseLayer: stm=" + repr(self.stm ) + ", ltm=" + repr(self.ltm )
    @property
    def type(self) -> str:
        return "(To fill)"



class L0(AbstractionLayer):

    def __init__(self, shortterm_kg: Optional[KnowledgeGraph]=None) -> None:
        super().__init__()
        self._longterm_knowledge = None
        if shortterm_kg is not None: self._shortterm_knowledge = shortterm_kg
    @property
    def kg(self) -> KnowledgeGraph:
        return self._shortterm_knowledge
    def __repr__(self):
        return "L0: stm=" + repr(self.stm )
    @property
    def type(self) -> str:
        return "L0"


class L1(AbstractionLayer):

    def __init__(self, shortterm_kg: Optional[KnowledgeGraph]=None) -> None:
        super().__init__()
        self._longterm_knowledge = None
        self._intension_map = None
        if shortterm_kg is not None: self._shortterm_knowledge = shortterm_kg
    @property
    def kg(self) -> KnowledgeGraph:
        return self._shortterm_knowledge
    @property
    def intension(self) -> dict:
        if self._intension_map is None: raise RuntimeError("L1 layer object has no calculated intension.")
        return self._intension_map
    @intension.setter
    def intension(self, new_intension: dict) -> None:
        self._intension_map = new_intension
    @property
    def type(self) -> str:
        return "L1"

    def __repr__(self):
        return "L1: stm=" + repr(self.stm ) +") intension="+repr(len(self._intension_map))

    def gen_intension_network(self, collapse: bool=True) -> nx.MultiDiGraph:
        """ 
            Generates the intension of the L1 Layer object in the format of a networkx graph (for easy 
                analysis/visualization).
            This method works only if the L1 <-> L2 linking is one-to-one on concepts: an L1 concept maps into one L2
                abstraction and vice versa. 

            Params:
                :collapse: Whether to collapse the mapped L2 concepts that appear repeated.
                    If this is True, if two different L1 concepts have the same intension, there will still be only
                    one L2 node in the graph. This means the result will be a veridic subset of the mapped L2 layer.
                    If this is False, different L1 concepts that map into the same L2 concept will generate DIFFERENT
                        nodes in the resulting graph. These nodes are differentiated by an accumulative index in the 
                        node name. The effective result is a graph that preserves the L1 relations but the nodes are 
                        abstracted away into its L2 counterparts.
            Returns:
                A networkx MultiDiGraph that represents the L1 intension.
        """
        if self._intension_map is None: raise RuntimeError("L1 layer object has no calculated intension.")
        net = nx.MultiDiGraph()
        ########
        ## Intension is not guaranteed to be injective, so multiple L1 concepts may be joined into a single node of this
        ##  network. For a generation that creates different nodes for different L1 concepts, use collapse=False
        class L2ConceptRenamer:
            def __init__(self) -> None:
                self.index = 0
                self.rename_map = {}
            def rename(self, l1_concept: str, l2_concept: str) -> str:
                if l1_concept in self.rename_map: return self.rename_map[l1_concept]
                new_name = f"{l2_concept}_{self.index}"
                self.index += 1
                self.rename_map[l1_concept] = new_name
                return new_name
        renamer = L2ConceptRenamer() if not collapse else None
        for key, val in self._intension_map.items():
            if type(key) == str: ## L1 node
                if type(val) == str: 
                    net.add_node(val if collapse else renamer.rename(key, val))
                elif type(val) == list: 
                    net.add_nodes_from(val if collapse else map(partial(renamer.rename, key), val))
                else: 
                    raise TypeError(f"Under key {key}: Don't know how to handle L2 extension {val} of type "+\
                    f"{type(val)}. Expected str or tuple type.")
            elif type(key) == tuple: ## L1 edge
                print(f"For key {key}")
                if type(val) == tuple:
                    if collapse: 
                        print(f"Adding edge {val}")
                        net.add_edge(*val)
                    else: 
                        print(f"Adding edges {val if len(val) < 5 else str(val[:5])+' ...'}")
                        net.add_edge(renamer.rename(key[0], val[0]), renamer.rename(key[1], val[1]))
                elif type(val) == list:
                    if collapse:
                        net.add_edges_from(val)
                    else:
                        net.add_edges_from(
                            list((renamer.rename(key[0], edge[0]), renamer.rename(key[0], edge[0])) for edge in val)
                        )
                else: 
                    raise TypeError(f"Under key {key}: Don't know how to handle L2 extension {val} of type " +\
                        f"{type(val)}. Expected tuple type.")
            else:
                raise TypeError(f"Don't know how to handle L1 intension of {key} of type {type(key)}")
        return net


class L2(AbstractionLayer):
    def __init__(self, longterm_kg: Optional[KnowledgeGraph]=None, shortterm_kg: Optional[KnowledgeGraph]=None) -> None:
        super().__init__()
        if longterm_kg is not None: self._longterm_knowledge = longterm_kg
        if shortterm_kg is not None: self._shortterm_knowledge = shortterm_kg
        self._extension_map:Optional[dict] = None
    
    @property
    def extension(self) -> dict:
        if self._extension_map is None: raise RuntimeError("L2 layer object has no calculated extension.")
        return self._extension_map
    @extension.setter
    def extension(self, new_extension: dict) -> None:
        self._extension_map = new_extension
    @property
    def type(self) -> str:
        return "L2"

    def __repr__(self):
        return "L2: (stm=" + repr(self.stm ) + ", ltm=" + repr(self.ltm )+") extension="+repr(self._extension_map)
    
    def gen_extension_network(self) -> nx.MultiDiGraph():
        """
            Generates the extension of the L2 Layer object in the format of a networkx graph (for easy 
                analysis/visualization).
            This method works only if the L1 <-> L2 linking is one-to-one on concepts: an L1 concept maps into one L2
                abstraction and vice versa. 

            Returns:
                A networkx MultiDiGraph that represents the L2 extension.
        """
        if self._extension_map is None: raise RuntimeError("L2 layer object has no calculated extension.")
        net = nx.MultiDiGraph()
        ## Extension is injective, so we may just directly build the graph
        for key, val in self._extension_map.items():
            if type(key) == str:
                if type(val) == str: net.add_node(val)
                elif type(val) == list: net.add_nodes_from(val)
                else: 
                    raise TypeError(f"Under key {key}: Don't know how to handle L2 extension {val} of type "+\
                    f"{type(val)}. Expected str or tuple type.")
            elif type(key) == tuple:
                if type(val) == tuple: net.add_edge(*val)
                elif type(val) == list: net.add_edges_from(val)
                else: 
                    raise TypeError(f"Under key {key}: Don't know how to handle L2 extension {val} of type " +\
                        f"{type(val)}. Expected tuple type.")
            else:
                raise TypeError(f"Don't know how to handle L2 extension of {key} of type {type(key)}")
        return net
