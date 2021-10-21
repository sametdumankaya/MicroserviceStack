
import logging
import multiprocessing
import queue    # here only for queue.Empty exception that is not part of multiprocessing.Queue
import sys
import networkx as nx
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union


from .inputworker import AlertstormInputWorker
from .inputworker import FileInputWorker
from dfre4net.knowledge import KnowledgeGraph
from dfre4net.layer import L0
from dfre4net.config import Config


class L0_Input:

    def __init__(self, config: Config, limit: Optional[int]=1000):

        self.q = multiprocessing.Queue(5)
        self.config = config
        self.limit = limit  ## Limit size for a batch of data
        self.count = 0  ## A counter used to calculate an unique id for alerts. Must be changed to use "oid" from alerts.
        
        ## Create the input worker according to the config
        if self.config.L0_input["type"] == "file":
            self.input_process = FileInputWorker(self.q, self.config.L0_input["src"], self.limit) ## To be update: must be configurable
        elif self.config.L0_input["type"] == "http":
            self.input_process = AlertstormInputWorker(self.q, self.config.L0_input["src"], self.limit) ## To be update: must be configurable
        else:
            raise Exception(f"Source '{self.config.L0_input['type']}' not supported!")

        # prefix for node label
        self.label_prefix = self.config.L0_input['node_label_prefix'] if 'node_label_prefix' in self.config.L0_input else 'label_'

    def start(self):

        self.input_process.start()

    def getL0(self) -> L0:
        
        while 1:
            
            elements = None
            try:
                elements = self.q.get(True, timeout=0.1)
            except queue.Empty:
                continue

            if type(elements)==dict and elements['EOF'] :
                break

            if type(elements) != list: raise OSError(f"The JSON is not a list of elements.")

            ## Graph
            g = nx.MultiDiGraph()

            ## input nodes properties added to each graph node
            node_props = self.config.L0_input['node_props'] if 'node_props' in self.config.L0_input else []

            ## Elements are ingested in labeled by enumeration
            for elmt in elements:

                elmt_label = f"{self.label_prefix}{self.count}"
                prop_dict = {}
                if len(node_props)>0:
                    for prop in node_props: prop_dict[prop] = str(elmt[prop]) if prop in elmt else str(None)
                else:
                    for prop in elmt: prop_dict[prop] = str(elmt[prop])
                g.add_node(elmt_label, **prop_dict)
                self.count += 1
            
            return L0(KnowledgeGraph(g))

        ## END OF DATA
        return None

    def stop(self):

        # terminate input worker
        self.input_process.terminate()
        self.input_process.join()
