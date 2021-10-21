import logging
from abc import ABC, abstractmethod
import heapq
import networkx as nx
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union


class KnowledgeGraph:

    def __init__(self, graph: Optional[nx.MultiDiGraph]=None) -> None:
        self.g = graph.copy() if graph is not None else nx.MultiDiGraph()
    def __repr__(self) -> str:
        return "KnowledgeGraph(nodes="+str(len(self.g.nodes))+", edges="+str(len(self.g.edges))+")"
    def __str__(self) -> str:
        return "KnowledgeGraph(nodes="+str(self.g.nodes)+", edges="+str(self.g.edges)+")"

class Concept:

    def __init__(self, _id: str) -> None:
        self.id = _id
    
    def __eq__(self, value: Any) -> bool:
        return self.id == str(value)
    def __ge__(self, value: Any) -> bool:
        return self.id > str(value) or self.id == str(value)
    def __gt__(self, value: Any) -> bool:
        return self.id > str(value)
    def __hash__(self):
        return self.id.__hash__()
    def __le__(self, value: Any) -> bool:
        return self.id < str(value) or self.id == str(value)
    def __lt__(self, value: Any) -> bool:
        return self.id < str(value)
    def __str__(self) -> str:
        return self.id
    def __repr__(self) -> str:
        return self.id

class Relation:

    def __init__(self, source_id: str, target_id: str) -> None:
        self.source_id = source_id
        self.target_id = target_id

    def __hash__(self):
        return self.__str__().__hash__()
    def __iter__(self) -> Iterator[str]:
        yield self.source_id
        yield self.target_id
    def __str__(self) -> str:
        return '('+self.source_id+', '+self.target_id+')'

class QueryResult:

    def __init__(self) -> None:
        self.concepts = set()
        self.relations = set()

    def add(self, elem: Union[Concept, Relation]) -> None:
        if type(elem) == Concept: self.concepts.add(str(elem))
        elif type(elem) == Relation: self.relations.add(str(elem))
        else: raise ValueError(f"Element {elem} is not a concept or relation.")

    ## TODO: remove(self, elem: Union[Concept, Relation]) method ??


class Query(ABC):
    """
        Abstract filter class that provides logic to separate concepts, relations or both between 2 partitions:
        the ones that obey the query and the ones that do not.
    """

    def __init__(self) -> None:
        self.result = QueryResult()
    
    @abstractmethod
    def apply(self, elem: Union[Concept, Relation]) -> bool:
        """
            Applies query logic to elem.
        """
        raise NotImplementedError

    def done(self) -> bool:
        """
            Returns if the query is done. Used for premature break of the query execution.
        """
        return False


class FirstNConceptsQuery(Query):
    """
        Extracts the first N elements of the query.
    """

    def __init__(self, max_concepts: int) -> None:
        super().__init__()
        if max_concepts < 0: raise ValueError('Maximum number of queried concepts should be positive.')
        self.max_alerts = max_concepts
        self.__count = 0
    
    def apply(self, elem: Union[Concept, Relation]) -> bool:
        """
            Add element to the query, if it's one of the first N concepts to be fed.
            Returns:
                True if the element is added (is one of the first N elements).
                False otherwise.
        """
        if type(elem) == Relation: return False
        if self.__count >= self.max_alerts: return False
        self.result.add(elem)
        self.__count += 1
        return True
    
    def done(self) -> bool:
        return self.__count >= self.max_alerts


class QueryRunner(ABC):
    """
        Abstract iterator class that iterates through a KnowledgeGraph, providing a
        sequential way to test for queries.

        This can be used as a node iterator, edge iterator or both. 
    """

    def __init__(self, kg: KnowledgeGraph) -> None:
        super().__init__()
        self.kg = kg

    @abstractmethod
    def __iter__(self) -> Iterator[Union[Concept,Relation]]:
        raise NotImplementedError

class DefaultNodeQueryRunner(QueryRunner):

    def __iter__(self):
        for node in self.kg.g.nodes:
            yield Concept(node)

class StringSizeProp(QueryRunner):

    """
        Extracts all nodes of a knowledge graph with a given property
        and for string only iterate over them following size of string (asc) of this property
    """

    def __init__(self, kg: KnowledgeGraph, prop_name: str) -> None:
        super().__init__(kg)
        self.prop_name = prop_name
        self.relevant_concepts = list(self.__extract_relevant(kg.g))
        #logging.debug(repr(self.relevant_concepts))
        self.__heap: List[Tuple[str, str]] \
            = sorted(map(lambda concept: (kg.g.nodes[str(concept)][self.prop_name], concept), self.relevant_concepts), key=len)

    def __extract_relevant(self, graph: nx.MultiDiGraph) -> Iterable[str]:
        """
            Extract all nodes of a graph that has the DFRE Severity property.
            Return:
                Iterable of NodePOinter. NodePointer is essentially an str,
                but can be any reference acceptable by networkx graphs.
        """
        for node, node_props in graph.nodes(data=True):
            if self.prop_name in node_props:
                if type(node_props[self.prop_name]) != str:
                    logging.error(f"[StringSizeProp] WARNING: Query runner found node {node} with "+\
                        f"{self.prop_name} property but with invalid value (not str). Ignoring..."
                    )
                else: yield Concept(node)

    def __iter__(self):
        #for node in self.relevant_concepts:
        while len(self.__heap) > 0:
            _, node = self.__heap.pop(0)
            #logging.debug(repr(node))
            yield node


class StringAlphabeticProp(QueryRunner):

    """
        Extracts all nodes of a knowledge graph with a given property
        and for string only iterate over them in alphabetical order (asc) of this property
    """

    def __init__(self, kg: KnowledgeGraph, prop_name: str) -> None:
        super().__init__(kg)
        self.prop_name = prop_name
        self.relevant_concepts = list(self.__extract_relevant(kg.g))
        #logging.debug(repr(self.relevant_concepts))
        self.__heap: List[Tuple[str, str]] \
            = sorted(map(lambda concept: (kg.g.nodes[str(concept)][self.prop_name], concept), self.relevant_concepts))

    def __extract_relevant(self, graph: nx.MultiDiGraph) -> Iterable[str]:
        """
            Extract all nodes of a graph that has the DFRE Severity property.
            Return:
                Iterable of NodePOinter. NodePointer is essentially an str,
                but can be any reference acceptable by networkx graphs.
        """
        for node, node_props in graph.nodes(data=True):
            if self.prop_name in node_props:
                if type(node_props[self.prop_name]) != str:
                    logging.error(f"[StringAlphabeticProp] WARNING: Query runner found node {node} with "+\
                        f"{self.prop_name} property but with invalid value (not str). Ignoring..."
                    )
                else: yield Concept(node)

    def __iter__(self):
        #for node in self.relevant_concepts:
        while len(self.__heap) > 0:
            _, node = self.__heap.pop(0)
            #logging.debug(repr(node))
            yield node

class DescendingProp(QueryRunner):
    """
        Extracts all nodes of a knowledge graph with a given property
        and iterate over them in descending order of this property
    """

    def __init__(self, kg: KnowledgeGraph, prop_name: str) -> None:
        super().__init__(kg)
        self.prop_name = prop_name
        self.relevant_concepts = list(self.__extract_relevant(kg.g))
        #logging.debug(repr(self.relevant_concepts))
        ## Join nodes and severities into tuples to construct heap
        ## Make severity negative to induce a max heap
        self.__heap: List[Tuple[Union[int,float], str]] \
            = list(map(lambda concept: (-kg.g.nodes[str(concept)][self.prop_name], concept), self.relevant_concepts))
        heapq.heapify(self.__heap)

    def __extract_relevant(self, graph: nx.MultiDiGraph) -> Iterable[str]:
        """
            Extract all nodes of a graph that has the DFRE Severity property.
            Return:
                Iterable of NodePOinter. NodePointer is essentially an str,
                but can be any reference acceptable by networkx graphs.
        """
        for node, node_props in graph.nodes(data=True):
            if self.prop_name in node_props:
                if type(node_props[self.prop_name]) not in (int, float):
                    logging.error(f"[DescendingProp] WARNING: Query runner found node {node} with "+\
                        f"{self.prop_name} property but with invalid value (not int nor float). Ignoring..."
                    )
                else: yield Concept(node)

    def __iter__(self) -> Iterator[Concept]:
        while len(self.__heap) > 0:
            _, node = heapq.heappop(self.__heap)
            #logging.debug(repr(node))
            yield node

class MatchingProp(QueryRunner):
    """
        Extracts all nodes of a knowledge graph with a given property
        and iterate over them in descending order of this property
    """

    def __init__(self, kg: KnowledgeGraph, prop_name: str, prop_value: str) -> None:
        super().__init__(kg)
        self.prop_name = prop_name
        self.prop_value = prop_value
        #self.graph = kg.g

    def __iter__(self) -> Iterator[Concept]:
        for node, node_props in self.kg.g.nodes(data=True):
            if self.prop_name in node_props:
                if node_props[self.prop_name] == self.prop_value:
                    yield Concept(node)

class MatchingPropWithOrder(QueryRunner):
    """
        Extracts all nodes of a knowledge graph with a given property
        and iterate over them in descending order of this property
    """

    def __init__(self, kg: KnowledgeGraph, match_prop_name: str, match_prop_value: str, order_prop_name: str) -> None:
        super().__init__(kg)
        self.match_prop_name = match_prop_name
        self.match_prop_value = match_prop_value
        self.order_prop_name = order_prop_name

        self.relevant_concepts = list(self.__extract_relevant(kg.g))
        #logging.debug(repr(self.relevant_concepts))
        ## Join nodes and severities into tuples to construct heap
        ## Make severity negative to induce a max heap
        self.__heap: List[Tuple[Union[int,float], str]] \
            = list(map(lambda concept: (-kg.g.nodes[str(concept)][self.order_prop_name], concept), self.relevant_concepts))
        heapq.heapify(self.__heap)

    def __extract_relevant(self, graph: nx.MultiDiGraph) -> Iterable[str]:
        """
            Extract all nodes of a graph that has the DFRE Severity property.
            Return:
                Iterable of NodePOinter. NodePointer is essentially an str,
                but can be any reference acceptable by networkx graphs.
        """
        mandatory_props = [self.match_prop_name, self.order_prop_name]
        for node, node_props in graph.nodes(data=True):
            if all(item in node_props for item in mandatory_props):
                if node_props[self.match_prop_name] == self.match_prop_value:
                    yield Concept(node)

    def __iter__(self) -> Iterator[Concept]:
        while len(self.__heap) > 0:
            _, node = heapq.heappop(self.__heap)
            #logging.info(f"node {repr(node)}, val={self.kg.g.nodes[node]['dfre_severity']}")
            yield node


def run_query(query: Query, runner: QueryRunner) -> QueryResult:
    """
        Executes a Query using a QueryRunner as engine.
        QueryRunner provides a stream of Concepts and/or Relations into the Query object.
        The Query object stores the memory of objects that satisfy the query and provides
            the result.
        
        Returns: 
            :QueryResult: A result description.
    """
    for elem in runner:
        query.apply(elem)
        if query.done(): break
    return query.result


def merge(*kgs: List[KnowledgeGraph]) -> KnowledgeGraph:
    """
        Merge a sequential list of KnowledgeGraphs with no overwriting,
        preserving the node that is added first.
        If 2 nodes/edges differ only on their properties, this doesn't merge them together.
    """
    if len(kgs) == 0: return KnowledgeGraph()
    return KnowledgeGraph(nx.compose_all(map(lambda kg: kg.g, kgs)))

def default_troubleshooting_l2_longtermKG() -> KnowledgeGraph:
    g = nx.MultiDiGraph()
    g.add_nodes_from([
        'SourceEndPoint',
        'TargetEndPoint'
        'Connection'
    ])
    g.add_edges_from([
        ('SourceEndPoint', 'Connection'),
        ('Connection', 'TargetEndPoint'),
        ('Connection', 'Connection')
    ])
    return KnowledgeGraph(g)

def default_alertstorm_l2_longtermKG() -> KnowledgeGraph:
    g = nx.MultiDiGraph()
    g.add_nodes_from([
        'AlertStorm',
        'Network',
        'TeleologicalCategorization',
        'Security',
        'Performance',
        'Management',
        'Functional'
    ])
    g.add_edges_from([
        ('AlertStorm', 'Network'),
        ('Network', 'TeleologicalCategorization'),
        ('NetworkCategorization', 'Performance'),
        ('NetworkCategorization', 'Security'),
        ('NetworkCategorization', 'Management'),
        ('NetworkCategorization', 'Functional')
    ])
    return KnowledgeGraph(g)
