import json
import logging
import pandas as pd
from pathlib import Path
import networkx as nx
import time
from itertools import islice

from .knowledge import KnowledgeGraph
from .layer import L0, L2
from .network import Network

def topology2network(filepath: Path) -> Network:
    if not filepath.exists: raise ValueError(f"The path {filepath} does not exist.")
    if not filepath.is_file: raise ValueError(f"File {filepath} is not a file.")
    return Network(nx.read_graphml(filepath.resolve()))

def topology2kg(filepath: Path) -> KnowledgeGraph:
    if not filepath.exists: raise ValueError(f"The path {filepath} does not exist.")
    if not filepath.is_file: raise ValueError(f"File {filepath} is not a file.")
    return KnowledgeGraph(nx.read_graphml(filepath.resolve()))

def regexcategories2L2(filepath: Path) -> L2:
    """
        This receives an xslx file and builds an L2 layer from the regex sheet information of it.
        The regex sheet has information about alerts title 
    """
    if not filepath.exists: raise ValueError(f"The path {filepath} does not exist.")
    if not filepath.is_file: raise ValueError(f"File {filepath} is not a file.")
    data_frame = pd.read_excel(filepath.resolve(), '2.2-TeleologicalCate.-regex')
    ## Graph:
    g = nx.MultiDiGraph()
    ## Assume structure:
    subcategory_count = 1
    for _, row in data_frame.iterrows():
        # Guarantee the L2 parents are on it
        subcategory_path = row['L2 LTM'].split('.')
        for i in range(len(subcategory_path)-1):
            if subcategory_path[i] != 'L2' and (subcategory_path[i], subcategory_path[i+1]) not in g.edges:
                g.add_edge(subcategory_path[i], subcategory_path[i+1])
        subcategory_parent = subcategory_path[-1]
        subcategory_label = f"SubCategory_Regex{subcategory_count}"
        g.add_node(subcategory_label, 
            src='teleo_regex',
            alert_count=0,#row['count'], 
            regex=row['regex'], 
            severity=row['severity'], 
            numeric_severity=row['Numeric severity'],
            category1=row['Category1'],
            l2_ltm=row['L2 LTM'],
            semantic_severity=row['semanticSeverity']
        )
        g.add_edge(subcategory_parent, subcategory_label)
        subcategory_count += 1
    return L2(KnowledgeGraph(g), KnowledgeGraph(g))

def uniqtitlecategories2L2(filepath: Path) -> L2:
    """
        This receives an xslx file and builds an L2 layer from the unique title sheet information of it.
        The unique title sheet has information about alerts title 
    """
    if not filepath.exists: raise ValueError(f"The path {filepath} does not exist.")
    if not filepath.is_file: raise ValueError(f"File {filepath} is not a file.")
    data_frame = pd.read_excel(filepath.resolve(), '2.1-TeleologicalCat-96')
    ## Graph:
    g = nx.MultiDiGraph()
    ## Assume structure:
    subcategory_count = 1
    for _, row in data_frame.iterrows():
        # Guarantee the L2 parents are on it
        subcategory_path = row['L2 LTM'].split('.')
        for i in range(len(subcategory_path)-1):
            if subcategory_path[i] != 'L2' and (subcategory_path[i], subcategory_path[i+1]) not in g.edges:
                g.add_edge(subcategory_path[i], subcategory_path[i+1])
        subcategory_parent = subcategory_path[-1]
        subcategory_label = f"SubCategory_UniqTitle{subcategory_count}"
        g.add_node(subcategory_label, 
            src='uniqtitle',
            alert_count=0,#row['count'], 
            title=row['title'], 
            severity=row['severity'], 
            numeric_severity=row['Numeric severity'],
            category1=row['Category1'],
            l2_ltm=row['L2 LTM'],
            semantic_severity=row['semanticSeverity']
        )
        g.add_edge(subcategory_parent, subcategory_label)
        subcategory_count += 1
    return L2(KnowledgeGraph(g), KnowledgeGraph(g))

def topology2L2(filepath: Path) -> L2:
    """
        This receives a graphml file and builds an L2 layer from the network topology on it.
        we add some attributes 'numeric_severity' and 'alert_count' 
    """
    if not filepath.exists: raise ValueError(f"The path {filepath} does not exist.")
    if not filepath.is_file: raise ValueError(f"File {filepath} is not a file.")
    ## Graph:
    g = nx.MultiDiGraph()
    ## Load source:
    g = nx.read_graphml(filepath.resolve())
    #g = nx.MultiDiGraph()
    nx.set_node_attributes(g, 'topology', 'src')
    nx.set_node_attributes(g, 0.0, 'numeric_severity')
    #nx.set_node_attributes(g, 'medium', 'semantic_severity')
    #nx.set_node_attributes(g, '', 'severity')
    #nx.set_node_attributes(g, 'Management', 'category1')
    nx.set_node_attributes(g, 0, 'alert_count')
    #graph_source = nx.Graph(graph_source)
    #for node, node_props in g.nodes(data=True):
    #    logging.info(node_props['src'])
    
    return L2(KnowledgeGraph(g), KnowledgeGraph(g))

def alternate_topology2L2(filepath1: Path, filepath2: Path) -> L2:
    """
        This receives a graphml file and builds an L2 layer from the network topology on it.
        we add some attributes 'numeric_severity' and 'alert_count' 
        Will replace device name and ip address with the one found on alerts.js
        FOR DEBUG ONLY
        filepath1 is out alerts database, typically 'TeleologicalCatSemanticSeverity.xlsx'
        filepath2 is the topology, typically "./troubleshoot/LargestCC_topologyBorg.graphml"
    """
    if not filepath1.exists: raise ValueError(f"The path {filepath1} does not exist.")
    if not filepath1.is_file: raise ValueError(f"File {filepath1} is not a file.")
    if not filepath2.exists: raise ValueError(f"The path {filepath2} does not exist.")
    if not filepath2.is_file: raise ValueError(f"File {filepath2} is not a file.")
    logging.info(f"filepath1={filepath1}")
    logging.info(f"filepath2={filepath2}")

    t0 = time.time()
    logging.info(f"loading of {filepath1} ...")
    alerts = []
    with open(filepath1, 'r') as f:
        while True:
            c = 0
            lines_gen = islice(f, 100)
            for line in lines_gen:
                alerts.append(json.loads(line))
                c=c+1
            if c==0:
                break
    logging.info(f"loading of {filepath1} in {round((time.time()-t0),3)}sec")
    logging.info(f"Extracting of unique device name list ...")
    t0 = time.time()
    uniqDeviceList = {}
    for elmt in alerts:
        if ("deviceName" not in elmt) or ("ipAddress" not in elmt): continue
        if str(elmt["deviceName"]) not in uniqDeviceList: uniqDeviceList[ str(elmt["deviceName"]) ] = str(elmt["ipAddress"])

    logging.info(f"Extracting of unique device name list with {len(uniqDeviceList)} elmts in {round((time.time()-t0),3)}sec")

    t0 = time.time()
    devicegraph = nx.read_graphml(filepath2.resolve())
    #for node, node_props in devicegraph.nodes(data=True):
    #    if node not in uniqDeviceList: uniqDeviceList.append(node)
    logging.info(f"loading of {filepath2} in {round((time.time()-t0),3)}sec")
    
    t0 = time.time()
    alternateGraph = nx.MultiDiGraph()
    deviceMappingList = {}  # store mapping between node in devicegraph and node in alternateGraph. Needed for edges.
    # Scan all devices and add corresponding nodes in our alternateGraph
    for node, node_props in devicegraph.nodes(data=True):
        prop_dict = {}
        for prop in node_props: prop_dict[prop] = str(node_props[prop])
        if len(uniqDeviceList) > 0:
            deviceItem = uniqDeviceList.popitem()
            prop_dict['management_address'] = deviceItem[1]
            alternateGraph.add_node(deviceItem[0], **prop_dict)
            deviceMappingList[node] = deviceItem[0]
        else: break
    nx.set_node_attributes(alternateGraph, 'topology', 'src')
    nx.set_node_attributes(alternateGraph, 0.0, 'numeric_severity')
    nx.set_node_attributes(alternateGraph, 0, 'alert_count')

    # Scan all devices and add corresponding nodes in our alternateGraph. Take in count the device name mapping in deviceMappingList
    for edge in devicegraph.edges():
        if (edge[0] not in deviceMappingList) or (edge[1] not in deviceMappingList):
            continue
        e0 = deviceMappingList[edge[0]]
        e1 = deviceMappingList[edge[1]]
        alternateGraph.add_edge(e0, e1)

    logging.info(f"mapping in {round((time.time()-t0),3)}sec")

    return L2(KnowledgeGraph(alternateGraph), KnowledgeGraph(alternateGraph))




