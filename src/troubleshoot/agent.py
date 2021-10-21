from abc import ABC, abstractmethod
import networkx as nx

from dfre4net.layer import L0, L1, L2
from dfre4net.network import NetworkPingProbe

class TroubleshootingAgent(ABC):
    ## TODO: Not super sure about this 'probe' injection approach. Other approach is to inject the network
    ##          and let the agent take care of its own tool, maybe in a polymorphic way. Right now we use
    ##          inheritance AND injection and that may get bloated.
    
    def __init__(self, l0: L0, l1: L1, l2: L2) -> None:
        self.l0 = l0
        self.l1 = l1
        self.l2 = l2


class PingTroubleshooter(TroubleshootingAgent):

    def __init__(self, l0: L0, l1: L1, l2: L2, probe: NetworkPingProbe) -> None:
        super().__init__(l0, l1, l2)
        self.probe = probe

    def execute(self, source: str, target: str) -> None:
        print(f"PingTroubleshooter: Start.\nSource={source}.\nTarget={target}")
        ## Get path between source and target from L1 augmented topology
        path = nx.shortest_path(self.l1.kg.g, source, target)
        #networkx returns equal distance nodes in the shortest path with (or). cleaning it here"
        temp_p=[]
        for p in path:
            if("(or)" not in p):
                temp_p.extend([p])
            else:
                temp_p.extend([p.split(" (or) ")[0]])
        path=temp_p    
        print(f"Analyze the shortest path path:\n{path}")
        for net_node in path[1:]: ## Ignore the source device
            print(f"Probe network node {net_node}...")
            if self.probe.ping(net_node): print("Node reachable.")
            else:
                print(f"Found unreachable network node {net_node}. Investigate it further.")
                break
        print(f"PingTroubleshooter: Finished.")


