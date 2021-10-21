from pathlib import Path
import networkx as nx
from typing import List, Optional

class Network:
    def __init__(self, desc: nx.Graph) -> None:
        self.desc = desc
        

class NetworkPingProbe:
    def __init__(self, net: Network, source_probe: str, faulty: Optional[str]=None) -> None:
        self.net = net
        self.source = source_probe # TODO: Not used, but conceptually makes sense to have it for now.
        self.faulty = faulty    # TODO: Already knowing what device is faulty is cheating, this is for simulation only.
    
    def ping(self, device: str) -> bool:
        """
            Simulates pinging device :device: from probe source :self.source:
        """
        if device not in self.net.desc.nodes: raise ValueError(f"Device {device} not in network being probed.")
        return self.faulty is None or device != self.faulty
