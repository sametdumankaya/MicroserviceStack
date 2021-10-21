from abc import ABC, abstractmethod
import logging
import heapq
import math
import networkx as nx
import re
import time
from typing import List, Tuple, Union

from dfre4net.knowledge import KnowledgeGraph
import dfre4net.knowledge as knowledge
from dfre4net.layer import L1, L2
import alertstorm.net as net
import alertstorm.layer as as_layer


def done() -> bool:
    """
        Definition of Done for the AlertStorm agent.
        Returns:
            True if the agent believes he has finished his job.
    """
    time.sleep(5)
    return False
    # raise NotImplementedError

def link(
    l1kg: KnowledgeGraph, 
    l2kg: KnowledgeGraph, 
    existing_intention: dict = None, 
    existing_extension: dict = None) -> Tuple[dict, dict]:
    """
        Build L1 <-> L2 interlayer connections (intension and extension) in the context of AlertStorm.
        L2 knowledge graph with a 'src' property are
            connected to L1 alert concepts according with this src.
        src:
            'teleo_regex': Teleological clustering of alerts via regexes applied to the alert titles.
                L1 alerts are linked into a node from this if the cluster regex matches the alert title.
            'uniqtitle': Direct mapping of a alert(identified by its title) into one teleological category.
                L1 alerts are linked into this if the cluster unique title is equal to the alert title.
            'topology': Direct mapping of an alert(identified by its deviceName) with one device (with name and ip adress).
    """
    intension = {}
    extension = {}
    nb_match = 0
    nb_match_topo = 0

    if existing_intention:
        intension =  {**intension, **existing_intention}
    if existing_extension:
        extension =  {**extension, **existing_extension}

    t0 = time.time()

    for l2cnpt, l2cnpt_prop in l2kg.g.nodes(data=True):
        if 'src' not in l2cnpt_prop: continue ## Ignore L2 concepts without this tag for now
        """logging.debug("---------------------")
        logging.debug("Agent::link(): l2cnpt="+repr(l2cnpt))
        logging.debug("Agent::link(): l2cnpt_prop="+repr(l2cnpt_prop))"""
        if l2cnpt not in extension: extension[l2cnpt] = []
        cnpt_src = l2cnpt_prop['src']
        for l1cnpt, l1cnpt_prop in l1kg.g.nodes(data=True):
            if l1cnpt not in intension: intension[l1cnpt] = []
            map_cnpts = False
            if cnpt_src == 'teleo_regex':
                map_cnpts = re.match(l2cnpt_prop['regex'], l1cnpt_prop['title']) is not None
            elif cnpt_src == 'uniqtitle':
                map_cnpts = l2cnpt_prop['title'] == l1cnpt_prop['title']
            elif cnpt_src == 'topology':
                if 'management_address' not in l2cnpt_prop:
                    continue
                map_cnpts = l2cnpt_prop['management_address'] == l1cnpt_prop['ipAddress']
                if map_cnpts:
                    #logging.debug(f"Match ip ipaddress {l1cnpt_prop['ipAddress']}/{l2cnpt_prop['management_address']} for device {l1cnpt_prop['deviceName']} and id {l2cnpt}")
                    nb_match_topo = nb_match_topo +1
            else: 
                logging.warning(f"Could not identify the source '{cnpt_src}' of the L2 concept '{l2cnpt}', ignore.")
            if map_cnpts:
                # print(f'Link {l1cnpt} and {l2cnpt}')
                intension[l1cnpt].append(l2cnpt)
                extension[l2cnpt].append(l1cnpt)
                nb_match = nb_match+1
                
    logging.info(f"nb_match={nb_match}, nb_match_topo={nb_match_topo}, in {round((time.time()-t0),3)}sec")

    return intension, extension


AvailbleProps = ['dfre_severity', 'numeric_severity', 'dfre_semantic_severity', 'semantic_severity',
                        'dfre_category', 'category1']
AvailableStrategy = ['default', 'string', 'inc']
def update_metric(
        target: str, 
        support: Union[str,List[str]], 
        targetKG: KnowledgeGraph, 
        supportKG: KnowledgeGraph, 
        targetProp: str,
        supportProp: str,
        strategy: str,
        options: dict={} ) -> None:

    """
        Updates a given property of a given target concept given its support following an update strategy.
        The update is done inplace on the target Knowledge Graph. 
    """
    #logging.debug("support="+repr(support))
    """if supportProp not in AvailbleProps:
        raise ValueError(f'supportProp {supportProp} not supported.')"""
    # Verify strategy validity
    if strategy not in AvailableStrategy:
       raise ValueError(f'Weighting strategy {strategy} not supported.')

    # Verify if targetProp exists
    if targetProp not in targetKG.g.nodes[target]: return
    # 
    node = targetKG.g.nodes[target]
    old_val = node[targetProp]
    # 
    contrib_text = ""
    novelty_matters_text = ""

    if strategy == 'default':
        new_val = 0
        if type(support) == list:
            contributing_nodes=[]
            for cnpt in support:
                if supportProp in supportKG.g.nodes[cnpt]:
                    #if debug: logging.info(f"cnpt={cnpt}, {supportProp}={supportKG.g.nodes[cnpt][supportProp]}")
                    new_val = new_val + supportKG.g.nodes[cnpt][supportProp]
                    contributing_nodes.append({cnpt: supportKG.g.nodes[cnpt][supportProp]})
            if len(contributing_nodes) > 0: 
                new_val /= len(contributing_nodes)
                contrib_text = f"from supportKG nodes {repr(contributing_nodes)}"
            else:
                #No update
                return
        else:
            if supportProp in supportKG.g.nodes[cnpt]:
                new_val = supportKG.g.nodes[support][supportProp]
                contrib_text = f"from supportKG node {{{support}: {supportKG.g.nodes[support][supportProp]}}}"
            else:
                #No update
                return
        if ('novelty_matters' in options) and \
            (options['novelty_matters'] == True) and \
            ('already_seen' in node) and \
            ('dfre_category' in node) and \
            (node['dfre_category'].strip()=='Security') and \
            (node['already_seen']=='False'):

            new_val = new_val/2
            novelty_matters_text = f", not new: val=val/2"
            #logging.debug(f"Novelty matters for node {node}")

    elif strategy == 'string':
        new_val = ''
        if type(support) == list:
            contributing_nodes=[]
            for cnpt in support:
                if supportProp in supportKG.g.nodes[cnpt]:
                    new_val = new_val + supportKG.g.nodes[cnpt][supportProp] + " "
                    contributing_nodes.append({cnpt: supportKG.g.nodes[cnpt][supportProp]})
            if len(contributing_nodes) > 0: 
                contrib_text = f"from supportKG nodes {repr(contributing_nodes)}"
            else:
                #No update
                return
        else:
            if supportProp in supportKG.g.nodes[cnpt]:
                new_val = supportKG.g.nodes[support][supportProp]
                contrib_text = f"from supportKG node {{{support}: {supportKG.g.nodes[support][supportProp]}}}"
            else:
                #No update
                return

    elif strategy == 'inc':
        new_val = node[targetProp] + 1
        contrib_text = f"for target node {{{target}: {node[targetProp]}}}"

    else:
        raise ValueError(f'Weighting strategy {strategy} not supported.')

    #logging.debug(f"New value for targetKG.g.nodes[{target}][{targetProp}]={new_val}")
    node[targetProp] = new_val
    node[targetProp + '_strat'] = strategy
    if targetProp + '_histo' not in node:
        node[targetProp + '_histo'] = f"Init val to {new_val}, strategy '{strategy}', contribution from {contrib_text}{novelty_matters_text};"
        if ('status' in node) and (node['status'] == ''): node['status']='updated'
    elif old_val!=new_val:
        node[targetProp + '_histo'] += f"Change val from {old_val} to {new_val}, strategy '{strategy}', contribution from {contrib_text}{novelty_matters_text};"
        if ('status' in node) and (node['status'] == ''): node['status']='updated'

def analyze_top_alerts(alerts: List[str], l1kg: knowledge.KnowledgeGraph, l2kg: knowledge.KnowledgeGraph):

    ## TODO: This works for L1 layer only right now.
    # Metrics: dfresev avg, top5 titles, top5 as sevs
    avg = math.inf
    dfresev_fn = lambda al: l1kg.g.nodes[al]['dfre_severity']
    if len(alerts) > 0: avg = sum(map(dfresev_fn, alerts)) / len(alerts)
    top5 = sorted(alerts, key=dfresev_fn, reverse=True)[:5]
    return (
        avg, 
        list(map(lambda al: l1kg.g.nodes[al]['title'], top5)), 
        list(map(lambda al: l1kg.g.nodes[al]['severity'], top5)),
    )

def process_phase(
        phase_nb: int,
        l2Prop: str, 
        l1Prop: str, 
        l2: KnowledgeGraph, 
        l1: KnowledgeGraph,
        strategy: Union['default', 'string'] = 'default', 
        query: Union['numeric_desc', 'string_len', 'string_alphabetic_asc'] = 'numeric_desc',
        config_options: dict = {},
        use_l2_feedback: bool = False) -> None:

    """
        Run a query on L2 stm to get top_concepts list, then update metrics of l1Prop on L1 nodes from l2Prop value of L2 nodes 
        that correspond to elmts of top_concepts. 
        If 'use_l2_feedback' is true, then run a query on L1 to find top_L1_elements (here = tops_alerts) then update metrics of
        l2Prop of L2 nodes based on l1Prop value of L1 nodes

    """
    # Determine which query fonction to use. We have choice between
    # knowledge.DescendingProp for int or float and
    # knowledge.StringAlphabeticProp or StringSizeProp for string
    query_fct = None
    if query=="numeric_desc":
        query_fct = knowledge.DescendingProp    ## Get top L2 from prior+context knowledge severity
    elif query=="string_alphabetic_asc":
        query_fct = knowledge.StringAlphabeticProp
    logging.debug(f"   [Phase {phase_nb}] Use query function '{query}'' ")

    logging.debug(f"   [Phase {phase_nb}] Select top L2 factors... ")
    query_result = knowledge.run_query(
        knowledge.FirstNConceptsQuery(config_options['l2decomp_batch']), 
        query_fct(l2.stm, l2Prop) ## Get top L2 from prior+context knowledge severity
    )
    l2_top_concepts = [ str(cnpt) for cnpt in query_result.concepts ]
    logging.info(f"   ... Retrieved {len(l2_top_concepts)} L2 concepts.")
    #logging.info(f"   ... l2_top_concepts= {repr(l2_top_concepts)} ")

    t0 = time.time()
    updatedl1 = set()
    for l2cnpt in l2_top_concepts:
        l2cnpt_extension = l2.extension[l2cnpt]
        #logging.debug("###AXT:: l2cnpt_extension for {0}={1}".format(l2cnpt, repr(l2cnpt_extension)))
        if type(l2cnpt_extension) == str:
            ## One single concept
            if l2cnpt_extension in updatedl1: continue ## Don't double update
            if l2cnpt_extension not in l1.intension: continue ## In case of batched l1, current l1cnpt can be in another l1 batch
            update_metric(
                l2cnpt_extension, 
                l1.intension[l2cnpt_extension], 
                l1.stm, 
                l2.stm, 
                l1Prop, 
                l2Prop,
                strategy
            )
            updatedl1.add(l2cnpt_extension)
        elif type(l2cnpt_extension) in (list, tuple):
            ## Multiple: do one by one
            for l1cnpt in l2cnpt_extension:
                if l1cnpt in updatedl1: continue ## Don't double update
                if l1cnpt not in l1.intension: continue ## In case of batched l1, current l1cnpt can be in another l1 batch
                update_metric(
                    l1cnpt, 
                    l1.intension[l1cnpt], 
                    l1.stm, 
                    l2.stm, 
                    l1Prop, 
                    l2Prop,
                    strategy
                )
                updatedl1.add(l1cnpt)
        else: raise TypeError(f'Invalid L2 extension type {type(l2cnpt_extension)}')
    t1 = time.time()
    logging.debug(f"   [Phase {phase_nb}] Updating top factors extension DFRESeverity in {round((t1-t0),3)}sec... Done!")

    if config_options['top_l1_stats']:
        ## Get and display top L1 alerts
        logging.debug(f"   [Phase {phase_nb}] Get top severe alerts...")
        query_result = knowledge.run_query(
            knowledge.FirstNConceptsQuery(config_options['l1decomp_batch']), 
            query_fct(l1.stm, l1Prop)  ## Get top alerts from our calculated DFRE severity
        )
        top_alerts = [ str(cnpt) for cnpt in query_result.concepts ]
        logging.debug(f"   ... Retrieved {len(top_alerts)} L1 alerts")
        avg, top5titles, top5_as_sevs = analyze_top_alerts(top_alerts, l1.stm, l2.stm)
        logging.debug(f"   ... Top alerts DFRESeverity average: {avg}")
        logging.debug(f"   ... Top 5 alerts' titles: {top5titles}")
        logging.debug(f"   ... Top 5 alerts' AlertStorm severities: {top5_as_sevs}")
        logging.debug(f"   [Phase {phase_nb}] Get top severe alerts... Done!")
    
    if use_l2_feedback:
        t0 = time.time()
        ## Feedback loop into L2 short term memory
        logging.debug(f"   [Phase {phase_nb}] Feedback update of L2 categories...")
        updatedl2 = set()
        for l1cnpt in l1.intension:
            #print(f"   ... L1[{l1cnpt}] -> L2({l1.intension[l1cnpt]})")
            l1cnpt_intension = l1.intension[l1cnpt]
            if type(l1cnpt_intension) == str:
                #if l2cnpt in updatedl2: continue ## Don't double update
                print(f"   ... ... ###STR L2({l1.intension[l1cnpt]})")
                update_metric(
                    l1cnpt_intension, 
                    l2.extension[l1cnpt_intension], 
                    l2.stm, 
                    l1.stm, 
                    l2Prop, 
                    l1Prop,
                    strategy
                )
            elif type(l1cnpt_intension) in (list, tuple):
                for l2cnpt in l1cnpt_intension:
                    #if l2cnpt in updatedl2: continue ## Don't double update
                    count = l2.stm.g.nodes[l2cnpt]['alert_count']
                    #print(f"   ... ... L2({l1.intension[l1cnpt]}).count = {count}")
                    update_metric(
                        l2cnpt, 
                        l2.extension[l2cnpt], 
                        l2.stm, 
                        l1.stm, 
                        "alert_count",
                        l1Prop,
                        'inc'
                    )
                    updatedl2.add(l1cnpt)
            else: raise TypeError(f'Invalid L1 intension type {type(l1cnpt_intension)}')
        t1 = time.time()
        logging.debug(f"   [Phase {phase_nb}] Feedback update of L2 categories in {round((t1-t0),3)}sec... Done!")
    #if agent.done(): break
    
#AvailableProcessingStrategy = ['formula', 'max', 'merge', 'radius', 'default']
def process2_phase(
        layers: dict,
        processing_stage: dict) -> None:

    """
        Process a stage according to the configuration
        Available processing strategy are:
        'formula': apply a formula on 'target_prop' property of 'target_kg' knowledge nodes
        'max': calculate the 'max' of a 'target_prop' property of 'target_kg' knowledge nodes. Will store in 'target_kg'.max
        'merge': merge 2 knowledge base 'target_kg' and 'support_kg' into 'target_kg'
        'radius': (under developement)
        'default': update metric on 'target_prop' property 'target_kg' from 'target_prop' property from concepts from 'support_kg', according to links intension/extension between the two.

    """
    phase_nb = processing_stage['id']
    logging.debug(f"   [Phase {phase_nb}] --> ")
    support_concepts = support_kg = target_kg = target_kg = None
    srcs = {}
    
    ## identify target/source, support_concepts/target_concepts from configuration
    if processing_stage['target_kg']=='l1':
        support_concepts = layers["l2"].extension
        support_kg = layers["l2"].stm
        target_concepts = layers["l1"].intension
        target_kg = layers["l1"].stm
    elif processing_stage['target_kg']=='l1_batch':
        support_concepts = layers["l2"].extension
        support_kg = layers["l2"].stm
        target_concepts = layers["l1_batch"].intension
        target_kg = layers["l1_batch"].stm
    elif processing_stage['target_kg']=='l2':
        # When we target l2, source can be either l1 or l1_batch, or none
        support_concepts = layers["l1"].intension
        support_kg = layers["l1"].stm
        if "support_kg" in processing_stage and processing_stage['support_kg']=="l1_batch":
            support_concepts = layers["l1_batch"].intension
            support_kg = layers["l1_batch"].stm
        target_concepts = layers["l2"].extension
        target_kg = layers["l2"].stm
    # Take in count a 'src' filter, if any
    if 'src' in processing_stage:
        srcs = processing_stage['src'].split(',')
    
    options = processing_stage['options'] if 'options' in processing_stage else {}

    t0 = time.time()

    ## process the stage
    if processing_stage['strategy'] == 'formula':

        process_operation_formula(  target_kg, 
                                    processing_stage['target_prop'], 
                                    processing_stage['formula'], 
                                    processing_stage['strategy'], 
                                    srcs)
        logging.info(f"   [Phase {phase_nb}] Updating {processing_stage['target_kg']}.{processing_stage['target_prop']} from formula in {round((time.time()-t0),3)}sec... Done!")
    
    elif processing_stage['strategy'] == 'max':

        process_operation_max(  target_kg, 
                                processing_stage['target_prop'], 
                                processing_stage['strategy'])
        logging.info(f"   [Phase {phase_nb}] Calculating max for {processing_stage['target_kg']}.{processing_stage['target_prop']} in {round((time.time()-t0),3)}sec... Done!")

    elif processing_stage['strategy'] == 'merge':

        process_operation_merge(    layers, 
                                    processing_stage['target_kg'], 
                                    processing_stage['support_kg'])
        logging.info(f"   [Phase {phase_nb}] merging {processing_stage['support_kg']} to {processing_stage['target_kg']} in {round((time.time()-t0),3)}sec... Done!")

    elif processing_stage['strategy'] == 'radius':

        process_operation_radius(   target_kg, 
                                    target_concepts,
                                    processing_stage['target_prop'], 
                                    support_kg,
                                    processing_stage['support_prop'], 
                                    srcs)
        logging.info(f"   [Phase {phase_nb}] Updating {processing_stage['target_kg']}.{processing_stage['target_prop']} from radius from {processing_stage['support_kg'] if 'support_kg' in processing_stage else None} in {round((time.time()-t0),3)}sec... Done!")

    else:

        process_operation_default(  target_kg, 
                                    support_kg, 
                                    support_concepts, 
                                    target_concepts, 
                                    processing_stage['target_prop'], 
                                    processing_stage['support_prop'], 
                                    processing_stage['strategy'], options)
        logging.info(f"   [Phase {phase_nb}] Updating {processing_stage['target_kg']}.{processing_stage['target_prop']} from {processing_stage['support_kg'] if 'support_kg' in processing_stage else None} in {round((time.time()-t0),3)}sec... Done!")
    
    logging.debug(f"   [Phase {phase_nb}] <-- ")

def process_operation_radius(target_kg: KnowledgeGraph, target_concepts: dict, target_prop: str, support_kg: KnowledgeGraph, support_prop: str, srcs: dict) -> None:

    """
        Process a target_prop in a radius 
    """
    # 1 - Update target_prop on target_kg graph from support_prop from support_kg
    for node, node_props in target_kg.g.nodes(data=True):

        # take in count of a 'src' filter, if any
        if len(srcs)>0 and ('src' in node_props) and (node_props['src'] not in srcs): continue

        if target_prop in node_props:
            if float(node_props['alert_count']) > 0:

                if node_props['alert_count'] != len(target_concepts[node]):
                    logging.warn(f"Inconsistent issue for node {node}, 'alert_count'={node_props['alert_count']} != len(target_concepts[node])={len(target_concepts[node])}")

                old_val = target_kg.g.nodes[node][target_prop]
                new_val = sum(support_kg.g.nodes[cnpt][support_prop] for cnpt in target_concepts[node])
                new_val /= len(target_concepts[node])
                target_kg.g.nodes[node][target_prop] = new_val
                #if old_val != new_val: logging.debug(f"Change val from {old_val} to {new_val}")
                
    # 2 - Create a graph from target_kg. Seems mandatory for nx.ego_graph
    G=nx.Graph(target_kg.g)

    # 3- loop again to add contribution from neighbourgs for each nodes. Do not use this in previous loop because we need to 
    # update all target_prop BEFORE calculate neighbourgs contribution. Otherwise we can add contribution from node
    # with improper target_prop value. 
    # Note: TODO we can loop again several time, here because add neighbouring contribution to a node will de facto 
    # modify by feedback neighbours for a further loop
    for node, node_props in target_kg.g.nodes(data=True):
        
        # take in count of a 'src' filter, if any
        if len(srcs)>0 and ('src' in node_props) and (node_props['src'] not in srcs): continue

        if target_prop in node_props:
            if float(node_props['alert_count']) > 0:

                sub_graph = nx.ego_graph(G, node, radius=1)
                old_val = target_kg.g.nodes[node][target_prop]
                neighbor_alert_count_sum = getNeighborSum(sub_graph, 'alert_count')
                neighbor_severity_sum = getNeighborSum(sub_graph, target_prop)
                contrib_val = neighbor_severity_sum / neighbor_alert_count_sum
                new_val = min( old_val + contrib_val, 1.0)
                target_kg.g.nodes[node][target_prop] = new_val
                if old_val != new_val: logging.debug(f"updating node {node}, neighbor alerts_sum={neighbor_alert_count_sum}, sever_sum={neighbor_severity_sum}, {old_val}->{new_val}")

def getNeighborSum(sub_graph:nx.Graph, attrib_name:str)->float:

    """Thus function sums all values of a given attrib_name for entire graph"""
    total=0
    for n in sub_graph.nodes(data=True):
        if(attrib_name in n[1]):
            total=total+float(n[1][attrib_name])
    return total

def process_operation_formula(target_kg: KnowledgeGraph, target_prop: str, formula: str, strategy: str, srcs: dict) -> None:

    """
        Apply a formula on all 'target_prop' property of 'target_kg' knowledge nodes
        The formula must store the result value on the global 'formula_value' variable. It will be assigned to the 
            'target_prop' property of 'target_kg' knowledge processed node
        Inside formula, you can use 
            - "node_props['<prop>']" to access to property <prop> of the current processd node
            - target_kg to access to the current processed knowledege. For exemple, target_kg.max
        Exemple of formula:
        global formula_value; ratio = {'critical': 1.0, 'error': 0.7, 'warning': 0.5}; formula_value = ((node_props['alert_count']/target_kg.max)*ratio[node_props['severity']]) if node_props['severity'] in ratio and target_kg.max>0.0 else 0.0;
    """

    for node, node_props in target_kg.g.nodes(data=True):

        # take in count of a 'src' filter, if any
        if len(srcs)>0 and ('src' in node_props) and (node_props['src'] not in srcs): continue

        if target_prop in node_props:
            old_value = node_props[ target_prop ]
            #if node=="SubCategory_UniqTitle109":
            #    logging.info(f"---node {node}, node_props={node_props}")
            try:
                global formula_value
                formula_value = 0
                cc = compile(formula, 'abc', 'exec')
                exec(cc)
                #logging.debug(f"formula result value={formula_value}")
                node_props[ target_prop ] = formula_value
                if (target_prop + '_histo') not in node_props:
                    node_props[target_prop + '_histo'] = f"Init value to {formula_value}, strategy '{strategy}', contribution from {cc};"
                    if ('status' in node_props) and (node_props['status'] == ''): node_props['status']='updated'
                    """if node=="SubCategory_UniqTitle109":
                        logging.info(f"node {node}, old_value={old_value}")
                        logging.info(f"node {node}, node_props={node_props}")
                        logging.info(f"node_props[{target_prop + '_histo'}]={node_props[target_prop + '_histo']}")"""
                elif old_value!=formula_value:
                    node_props[target_prop + '_histo'] += f"Change val from {old_value} to {formula_value}, strategy '{strategy}', contribution from {cc};"
                    if ('status' in node_props) and (node_props['status'] == ''): node_props['status']='updated'
            except Exception as e:
                logging.error(f"Failed to apply formula, err={repr(e)} for node {node}={node_props}")

def process_operation_max(target_kg: KnowledgeGraph, target_prop: str, strategy: str) -> None:

    """
        Calculate the max value of a prop on target_kg knowledge nodes.
        The max value is assign to target_kg 
    """
    target_kg.max = get_metric(target_kg, target_prop, strategy)
    logging.debug(f"max(2): {target_kg.max}")

def process_operation_merge(layers: dict, layerto: str, layerfrom: str) -> None: 

    """
        merge 2 knowledge base layers['layerfrom'] and layers['layerto'] into layers['layerto'] 
    """
    #logging.debug(f"Current L1 status 1: {repr(layers['l1'])}")
    logging.debug(f"Merge {layerfrom} to {layerto}")
    layers[layerto] = as_layer.merge_l1(layers[layerto], layers[layerfrom])
    #logging.debug(f"Current L1 status: {repr(layers['l1'])}")

def process_operation_default(
    target_kg: KnowledgeGraph, 
    support_kg: KnowledgeGraph, 
    support_concepts: dict, 
    target_concepts: dict, 
    target_prop: str, 
    support_prop: str, 
    strategy: str, options: dict={}, phase_nb: int=0) -> None:

    """
        update metric on 'target_prop' property 'target_kg' from 'target_prop' property from concepts from 'support_kg', 
        according to links intension/extension between the two.
    """
    updated = set()
    for concept in support_concepts:
        targets = support_concepts[concept]
        if type(targets) == str:
            ## One single concept
            #if targets in updated: continue ## Don't double update
            if targets not in target_concepts: continue ## In case of batched l1, current target can be in another l1 batch
            update_metric(
                targets, 
                target_concepts[targets], 
                target_kg, 
                support_kg, 
                target_prop, 
                support_prop,
                strategy, options
            )
            updated.add(targets)
        elif type(targets) in (list, tuple):
            ## Multiple: do one by one
            for target in targets:
                #if target in updated: continue ## Don't double update
                if target not in target_concepts: continue ## In case of batched l1, current target can be in another l1 batch
                update_metric(
                    target, 
                    target_concepts[target], 
                    target_kg, 
                    support_kg, 
                    target_prop, 
                    support_prop,
                    strategy, options
                )
                updated.add(target)
        else: raise TypeError(f'Invalid L2 extension type {type(target)}')


def detectUnclassified(l1kg: KnowledgeGraph, intension: dict, count_max: int = 5) -> None:
    
    """
        Detect top unclassified elements for L1 (i.e. nodes that have no intension)

    """
    no_match = {}
    for l1cnpt, l1cnpt_prop in l1kg.g.nodes(data=True):
        if len(intension[l1cnpt])==0:
            if l1cnpt_prop["title"] not in no_match:
                no_match[l1cnpt_prop["title"]]=0
            else:
                no_match[l1cnpt_prop["title"]]+=1

    __heap: List[Tuple[int, str]] = list(map(lambda title: (-no_match[title], title), no_match))
    heapq.heapify(__heap)

    count = 0
    logging.debug(f"Detect Top {count_max} unclassified elemts")
    while (len(__heap)>0 and count<count_max):
        nb, title = heapq.heappop(__heap)
        logging.debug(f"... {-nb} alerts for title='{title}'")
        count+=1

def get_metric(kg: KnowledgeGraph, prop: str, strategy: Union['max', 'min', 'avg']) -> int:
    
    """
        Calculate some global metric from a property 'prop' of 'kg' nodes. 
        Available strategy are 'max', 'min', 'avg'

    """
    val = None
    if strategy == 'max':
        for node, node_props in kg.g.nodes(data=True):
            if prop in node_props:
                if (val == None) or (node_props[prop] > val):
                    val = node_props[prop]
    elif strategy == 'min':
        for _, node_props in kg.g.nodes(data=True):
            if prop in node_props:
                if (val == None) or (node_props[prop] < val):
                    val = node_props[prop]
    elif strategy == 'avg':
        pass
    else:
        raise ValueError(f'strategy {strategy} not supported.')

    return val

def resetKnowledgeStatus(kg: KnowledgeGraph) -> None:
    
    nx.set_node_attributes(kg.g, '', 'status')

def test(kg: KnowledgeGraph) -> None:
    
    """
        Calculate some global metric from a property 'prop' of 'kg' nodes. 
        Available strategy are 'max', 'min', 'avg'

    """
    for node, node_props in kg.g.nodes(data=True):
        #if "rank_new" in node_props:
        #    if node_props["rank_new"] != 0:
        #        logging.debug(f"find a rank_new={node_props['rank_new']} for node {node}")
        """if "already_seen" in node_props:
            if node_props["already_seen"] == "False":
                if node != 'alert_4863':
                    logging.debug(f"find a already_seen=({node_props['already_seen']}) for '{node}' title='{node_props['title'][:50]}' device={node_props['problem_id']}")
                for node2, node2_props in kg.g.nodes(data=True):
                    if node_props["deviceId"]==node2_props["deviceId"] and node_props['title']==node2_props['title']:
                        if node != 'alert_4863':
                            logging.debug(f"... on '{node2}'({node2_props['already_seen']}). title='{node2_props['title'][:50]}', problem_id={node2_props['problem_id']}")
        """
        if "already_seen" in node_props:
            if node_props["already_seen"] == "False":
                c = 0
                for node2, node2_props in kg.g.nodes(data=True):
                    if (node!=node2) and (node_props["deviceId"]==node2_props["deviceId"]) and (node_props['title']==node2_props['title']):
                        if c == 0:
                            logging.debug(f"find '{node}' with already_seen=({node_props['already_seen']}), title='{node_props['title'][:50]+ '...'}', devdateice={node_props['date']}")
                        logging.debug(f"... and '{node2}'({node2_props['already_seen']}). title='{node2_props['title'][:50]+ '...'}', date={node2_props['date']}")
                        c += 1
        if 'CSC' in node_props["title"]:
            logging.debug(f"find a bug in '{node}', title={node_props['title']}")
