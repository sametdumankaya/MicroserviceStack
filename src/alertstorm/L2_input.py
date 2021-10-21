import logging
import sys
import time
import networkx as nx
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union


import dfre4net.ingest as ingest
import dfre4net.layer as layer
import dfre4net.knowledge as knowledge
from dfre4net.knowledge import KnowledgeGraph
from dfre4net.layer import L2
from dfre4net.config import Config

class L2_Input:

    def __init__(self, config: Config=None):

        self.config = config
        self.count = 0  ## A counter used to calculate an unique id for alerts. Must be changed to use "oid" from alerts.
        
    def getL2(self) -> L2:
        
        ## Load our various knowledge bases, each of them will be tagged with a source attibute
        l2_regex = ingest.regexcategories2L2(self.config.L2_input["src"])
        l2_uniq  = ingest.uniqtitlecategories2L2(self.config.L2_input["src"])
        #l2_topo  = ingest.topology2L2(self.config.L2_input["src2"])
        l2_topo  = ingest.alternate_topology2L2(self.config.L0_input["src"], self.config.L2_input["src2"])
        logging.debug(l2_topo)

        ### Merge all in one
        l2 = layer.L2(
            knowledge.merge(l2_regex.ltm, l2_uniq.ltm, l2_topo.ltm),
            knowledge.merge(l2_regex.stm, l2_uniq.stm, l2_topo.stm)
        )       
        l2.extension = {}

        ### Dump initial state if needed
        if self.config.parameters["dump_l2"]:
            logging.debug(f'... Dump initial L2')
            nx.write_graphml(l2_regex.ltm.g, 'alertstorm_l2_regex.graphml')
            nx.write_graphml(l2_uniq.ltm.g, 'alertstorm_l2_uniq.graphml')
            nx.write_graphml(l2.ltm.g, 'alertstorm_l2_ltm.graphml')
            nx.write_graphml(l2.stm.g, 'alertstorm_l2_stm.graphml')

        ### Make some checks, identify and display list of source
        t0 = time.time()
        srcs = {}
        for node, node_props in l2.stm.g.nodes(data=True):
            if 'src' not in node_props: 
                logging.warn(f"An l2 node {node} without 'src' tag has been found!!!")
                logging.debug(f"{node} = {node_props}")
                continue
            src = node_props['src']
            if src not in srcs:
                srcs[src] = 1
            else:
                srcs[src] = srcs[src] + 1
        for src in srcs:
            logging.info(f"Current L2 contains source {src} with {srcs[src]} elements")
        logging.info(f"Parsing L2 took {round((time.time()-t0),3)}sec")
        
        return l2

    def getEmpty(self) -> L2:

        g = nx.MultiDiGraph()
        l2 = L2(KnowledgeGraph(g), KnowledgeGraph(g))
        l2.extension = {}
        return l2

