import networkx as nx
import os
from pathlib import Path
from random import choice
import sys
from typing import List

import dfre4net.ingest as ingest
import dfre4net.knowledge as knowledge
import dfre4net.layer as layer
import dfre4net.network as network
import troubleshoot.agent as agent
import troubleshoot.layer as trbsht_layer

USE_CASE_ID = 'troubleshoot'
DIR = Path(os.path.abspath(__file__)).parent
NETWORK_TOPOLOGY_FILEPATH = DIR / Path('./LargestCC_topologyBorg_withAlerts.graphml')

def output_interlayerlinks(l2_ext_net, l1_int_net, l1_int_net_nocollapse) -> None:
    nx.write_graphml(l2_ext_net, 'l2_extension_LargestCC_topologyBorg_withAlerts.graphml')
    nx.write_graphml(l1_int_net, 'l1_intension_LargestCC_topologyBorg_withAlerts.graphml')
    nx.write_graphml(l1_int_net_nocollapse, 'l1_intension_nocollapse_LargestCC_topologyBorg_withAlerts.graphml')

def main(args: List[str]) -> None:
    print(f"Loading network topology from {NETWORK_TOPOLOGY_FILEPATH.resolve()}")
    ## Load Network
    HnM_network = ingest.topology2network(NETWORK_TOPOLOGY_FILEPATH)
    ## Load L0 knowledge graph from network topology
    l0_kg = ingest.topology2kg(NETWORK_TOPOLOGY_FILEPATH)
    ## Create L0 abstraction layer
    l0 = layer.L0(l0_kg)
    ## Create L2 abstraction layer from custom troubleshooting knowledge
    print("Generate initial L2 with crafted knowledge")
    l2 = layer.L2(knowledge.default_troubleshooting_l2_longtermKG())
    ## Derive L1 from combining L0 context and L2 knowledge
    print("Derive L1 layer from L2 long term knowledge and contextual L0...")
    l1 = trbsht_layer.derive_l1(l0, l2)

    ## Choose 2 random L1 nodes
    source = None
    target = None
    faulty = None
    MIN_PATH_LEN = 5
    MAX_PATH_LEN = 20
    print("Randomly select 2 nodes...")
    while True:
        source = choice(list(l1.kg.g.nodes))
        target = source
        while target == source: target = choice(list(l1.kg.g.nodes()))
        shortest_path = nx.shortest_path(l1.kg.g, source, target)
        if len(shortest_path) >= MIN_PATH_LEN and len(shortest_path) <= MAX_PATH_LEN:
            faulty = choice(shortest_path[1:]) ## Source must not contain the problem
            break
    print(f"Randomly selected nodes source: {source} and target: {target}")

    ## The operator used to connect L1 and L2
    interlayer_builder = trbsht_layer.E2EInterLayerLinkBuilder(source, target)
    interlayer_builder.build(l1, l2)
    ## Output result of interlayer mapping
    output_interlayerlinks(l2.gen_extension_network(), l1.gen_intension_network(), l1.gen_intension_network(False))
    ## Troubleshooting Agent
    trblshoot_agent = agent.PingTroubleshooter(l0, l1, l2, network.NetworkPingProbe(HnM_network, source, faulty))
    trblshoot_agent.execute(source, target)

if __name__ == '__main__':
    main(sys.argv[1:])
