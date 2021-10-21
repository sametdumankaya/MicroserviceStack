from abc import ABC, abstractmethod
import enum
import networkx as nx
from typing import List

from .layer import L0, Lstar

class NetworkStatus(enum.Enum):
    WORKING = 'working'
    BROKEN = 'broken'
    def __str__(self) -> str:
        self.value

class NetworkDescription:
    """ Network description in concept layers. """

    def __init__(self, l0: L0, l1: nx.DiGraph, l2: nx.MultiDiGraph, lstar: Lstar) -> None:
        self.l0 = l0
        self.l1 = l1
        self.l2 = l2
        self.lstar = lstar
        self._status = NetworkStatus.WORKING
    
    @property
    def status(self) -> NetworkStatus:
        return self._status
    
    def toggle_status(self) -> None:
        self._status = NetworkStatus.BROKEN if self.status == NetworkStatus.WORKING else NetworkStatus.WORKING
        if self._status == NetworkStatus.BROKEN: self.lstar.state = Lstar.L2_BROKEN
        else: self.lstar.state = Lstar.L2_WORKING

class NetworkAnomaly(ABC):
    """ Description of a Network Anomaly with its required layer portions. """
    def __init__(self, broken_lstar: nx.DiGraph, broken_l0: nx.DiGraph) -> None:
        self.broken_lstar = broken_lstar
        self.broken_l0 = broken_l0

class TroubleshootingAgent(ABC):
    """ DFRE for networking agent. """

    def __init__(self, l2_expertise: nx.DiGraph, net_desc: NetworkDescription) -> None:
        self.l2_expertise = l2_expertise
        self.net_desc = net_desc
    
    @abstractmethod
    def repair(self, anomaly: NetworkAnomaly) -> None:
        raise NotImplementedError

class TriggeringSystem(ABC):
    """ Abstract external agent, triggers events in L*. """
    @abstractmethod
    def collect(self) -> NetworkAnomaly:
        """ Generates an network anomaly description in the terms of abstraction layers. """
        raise NotImplementedError
