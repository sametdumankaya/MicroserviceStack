import heapq
import networkx as nx
import time
from typing import List

from .troubleshoot import NetworkAnomaly, NetworkDescription, NetworkStatus, TriggeringSystem, TroubleshootingAgent
from .layer import generate_l1, L0, Lstar

USE_CASE_ID = 'troubleshoot_basic'

def __create_uc1_l2_ontology() -> nx.MultiDiGraph:
    mem = nx.MultiDiGraph()
    mem.add_nodes_from([
        (
            'User',
            {
                'purpose': 'To use devices',
                'properties': ['location'],
                'functions': ['operate_device']
            }
        ),
        (
            'Laptop',
            { 
                'purpose': 'To enable user to run CLI commands',
                'properties': ['ip', 'mac', 'location'],
                'functions':['ping']
            }
        ),
        (
            'Port',
            {
                'purpose': 'To connect devices',
                'properties': ['port_number', 'name'],
                'functions': ['connect']
            }
        ),
        (
            'Switch',
            {
                'purpose': 'To connect devices',
                'properties': ['ip', 'device_name'],
                'functions': []
            }
        ),
        (
            'Printer',
            {
                'purpose': 'To print documents',
                'properties': [],
                'functions': ['print']
            }
        ),
        (
            'Endpoint',
            {
                
            }
        )
    ])
    mem.add_edges_from([
        ('User', 'Laptop', 'has'),
        ('User', 'Laptop', 'near'),
        ('Laptop', 'Port', 'connection'),
        ('Port', 'Switch', 'on'),
        ('Port', 'Port', 'connection'),
        ('Printer', 'Port', 'connection')
    ])
    return mem

def create_default_uc1_l0() -> L0:
    """ Creates the initial L0 layer for Use Case 1 with:
        --> Topology information.
        --> Device labeling.
        --> User identification.
    """
    l0 = L0([
        'Jane',
        # Devices
        'Laptop1',
        'Laptop2',
        'Printer1',
        # Ports
        *list(f'Port{i}' for i in range(1,9)),
        # Switches
        'Switch1',
        'Switch2',
        # Etc
        'MailServer1'
    ],[
        ('Jane', 'Laptop1', {'relation': 'has'}),
        ('Jane', 'Laptop2', {'relation': 'near'}),
        ('Laptop1', 'Port1', {'relation': 'connection'}),
        ('Laptop2', 'Port2', {'relation': 'connection'}),
        ('Port1', 'Switch1', {'relation': 'on'}),
        ('Port2', 'Switch1', {'relation': 'on'}),
        ('Port7', 'Switch1', {'relation': 'on'}),
        ('Port6', 'Switch1', {'relation': 'on'}),
        ('MailServer1', 'Port6', {'relation': 'connection'}),
        ('Port3', 'Switch1', {'relation': 'on'}),
        ('Port3', 'Port4', {'relation': 'connection'}),
        ('Port4', 'Switch2', {'relation': 'on'}),
        ('Port8', 'Switch2', {'relation': 'on'}),
        ('Port5', 'Switch2', {'relation': 'on'}),
        ('Printer1', 'Port5', {'relation': 'connection'})
    ],{
        'Jane': 'User',
        'Laptop1': 'Laptop',
        'Laptop2': 'Laptop',
        'Printer1': 'Printer',
        **{f"Port{i}": 'Port' for i in range(1,9)},
        'Switch1': 'Switch',
        'Switch2': 'Switch',
        'MailServer1': 'MailServer'
    })
    return l0

class UC1Anomaly(NetworkAnomaly):
    """ Description of the Anomaly treated by UC1. """

    def __init__(self, broken_lstar: nx.DiGraph, broken_l0: nx.DiGraph, source: str, target: str) -> None:
        super().__init__(broken_lstar, broken_l0)
        self.source = source
        self.target = target

class UC1TroubleshootingAgent(TroubleshootingAgent):
    """ UC1 Troubleshooting agent. 
        Has troubleshooting knowledge about:
        * Device pinging
        * OS replacement
        * Source device replacement
    """

    def __execute(self, action:str, *args) -> bool:
        """
            For UC1, this contains the result of possible actions. Ideally we should simulate the actions, here we just
                pre-store the results
            
            Returns True/False since all actions have binary result type.
        """
        if action == 'ping':
            if len(args) < 1: raise ValueError('Ping requires the concept being pinged')
            pinged = args[0]
            return pinged in ('Laptop1', 'Port1', 'Switch1', 'Port3') ## Devices reachable, Port4 is problematic 
        elif action == 'change_os':
            ## This option does not help
            return False
        elif action == 'replace_dev':
            ## This option does not help
            return False
        else: raise ValueError(f"Unknown troubleshooting action {action}")

    def __init__(self, net_desc: NetworkDescription) -> None:
        g = nx.DiGraph()
        g.add_nodes_from([
            'SourceEndPoint',
            'Connection'
        ])
        g.add_edges_from([
            ('SourceEndPoint', 'Connection'),
            ('Connection', 'TargetEndPoint'),
            ('Connection', 'Connection') ## <-- Not necessary for UC1
        ])
        super().__init__(g, net_desc)
        self.l2_expertise_to_l2_ontology = nx.DiGraph()
        self.l2_expertise_to_l2_ontology.add_edges_from([
            ('SourceEndPoint', 'Laptop'),
            ('TargetEndPoint', 'Printer'),
            ('Connection', 'Printer'),
            ('Connection', 'Switch'),
            ('Connection', 'Port')
        ])
        ## Map of troubleshooting options to standard action cost
        self.troubleshoot_costs = {
            'ping': 1,
            'change_os': 5,
            'replace_dev': 10
        }
    
    def __pprint_path(self, path: List[str]) -> None:
        print("Source/Target path:")
        for i in range(len(path)-1):
            print(f"{path[i]} --> {path[i+1]}")
    
    def repair(self, anomaly: UC1Anomaly) -> None:
        print("Initiate troubleshooting for Use Case 1.\n")
        #################
        ## Pre-processing for ping action
        ## Find all paths between source and target on l1.
        topology_graph = nx.Graph()
        for node1, node2, semantics in self.net_desc.l1.edges(data=True):
            if semantics['relation'] in ('has', 'on', 'connection'): topology_graph.add_edge(node1, node2)
        l1_paths = [list(path) for path in nx.all_simple_paths(topology_graph, anomaly.source, anomaly.target)]
        if len(l1_paths) == 0: raise RuntimeError("No paths between source and target.")
        if len(l1_paths) > 1: raise RuntimeError("Don't know how to handle multiple paths at the moment.")
        self.__pprint_path(l1_paths[0])
        ## Ping binary search pointers for given path 
        ##  Analyze segment of path starting at 0 and ending at len(l1_paths[path_iter])-1
        ping_iter = (0, len(l1_paths[0])-1) 
        ## Unique list of reachable/unreachable devices
        reachable = set()
        unreachable = set()

        #################
        ## Pre-processing for change_os action
        ## Find all L1 concepts mapped into the anomaly source object, in UC1 this will be 'Laptop1'
        l1_changeos_candidates = [anomaly.source]

        #################
        ## Pre-processing for replace_dev action
        ##  Find all L2 ontology concepts that 'SourceEndPoint' is mapped into. In UC1 this will be only 'Laptop'
        l2_sourceendpoint_ontology = set(l2_concept for l2_concept in self.l2_expertise_to_l2_ontology.neighbors('SourceEndPoint'))
        ## Find all L1 concepts mapped into these L2 ontology abstractions, in UC1 this will be 'Laptop1' and 'Laptop2'
        l1_replacedev_candidates = []
        for l1_concept in self.net_desc.l1.nodes:
            if (l1_concept != anomaly.source # Can't replace something for itself
                and self.net_desc.l0.tag_dict[l1_concept] in l2_sourceendpoint_ontology):
                l1_replacedev_candidates.append(l1_concept)
        
        #################
        ## Troubleshooting loop data structures
        ## Queue for dynamic selection of troubleshooting action
        priority_queue = [
            (self.troubleshoot_costs[key], self.troubleshoot_costs[key], key) for key in self.troubleshoot_costs.keys()
        ]
        heapq.heapify(priority_queue)

        ## Don't allow repetition of troubleshooting option
        ## Saves pairs (<action>, DS(<l1 concepts involved>)): <result> where DS = tuple when order matters and set 
        ##  when order does not matter and no DS if it's only one concept.
        executed = {}

        #################
        ### Troubleshooting loop
        while True:
            action_acc_cost, action_cost, action_name = heapq.heappop(priority_queue)
            print(f"\nAgent action: {action_name}. Accumulated cost: {action_acc_cost}")
            if action_name == 'ping':
                ## Get L2 intention of the L1 concept in the path
                concept_idx = int((ping_iter[0] + ping_iter[1])/2)
                l1_concept = l1_paths[0][concept_idx]
                ## Check if this action hasn't been executed before
                if ('ping', l1_concept) not in executed:
                    l1_L2projection = self.net_desc.l0.tag_dict[l1_concept]
                    ## Verify if domain expertise allows pinging (to be "pingable" it should be mapped into 'Connection' or 'EndPoint')
                    if (('Connection', l1_L2projection) in self.l2_expertise_to_l2_ontology.edges
                        or ('EndPoint', l1_L2projection) in self.l2_expertise_to_l2_ontology.edges):
                        print(f"Executing ping(L1.{l1_concept})...")
                        time.sleep(5)
                        result = self.__execute('ping', l1_concept)
                        print('Result: ' + f"Device {l1_concept} reachable" if result else f"Device {l1_concept} unreachable")
                        if result: reachable.add(l1_concept)
                        else: unreachable.add(l1_concept)
                        executed[('ping', l1_concept)] = result
                    else:
                        print(f"Concept {l1_concept} not appropriate for ping. Skip.")
                        time.sleep(5)
                else:
                    print(f"Use cached result: ping(L1.{l1_concept}) = {executed[('ping', l1_concept)]}")
                result = executed[('ping', l1_concept)]
                if ping_iter[0] == ping_iter[1]:
                    ## Binary search is done for this path
                    print("Ping analysis finished.")
                    if result:
                        # Everything is reachable, no problems
                        print("Inconclusive: found no connection problems.")
                        continue ## Don't add new ping action to prioritye_queue
                    else:
                        print(f"Connection problems suggest failure on {l1_concept}.")
                        self.net_desc.toggle_status()
                        break
                else:
                    ## Update binary search pointers for current path
                    if result: 
                        ## Device is reachable, so analyze only the path after it
                        # Don't include the device itself since we want to find the closest False result
                        ping_iter = (concept_idx+1, ping_iter[1])
                    else:
                        ## Device unreachable, the problem must be somewhere until it
                        ping_iter = (ping_iter[0], concept_idx)
            elif action_name == 'change_os':
                device_to_change_os = l1_changeos_candidates.pop()
                if ('change_os', device_to_change_os) not in executed:
                    print(f"Changing OS of device {device_to_change_os}...")
                    time.sleep(5)
                    result = self.__execute('change_os', device_to_change_os)
                    print('Result:' + f"Device with new OS presents no errors." if result else f"Device with new OS presents the same problem.")
                    if result:
                        print(f"Recommended action: Replace operating system or do a fresh intallation.")
                        self.net_desc.toggle_status()
                        break
                    executed[('change_os', device_to_change_os)] = result
                if len(l1_changeos_candidates) == 0:
                    ## No more replace device candidates, don't put back in queue
                    continue
            elif action_name == 'replace_dev':
                new_device = l1_replacedev_candidates.pop()
                if ('replace_dev', new_device) not in executed:
                    print(f"Replacing device {anomaly.source} for {new_device}...")
                    time.sleep(5)
                    result = self.__execute('replace_dev', new_device)
                    print('Result:' + f"Device {new_device} presents no errors." if result else f"Device {new_device} presents the same problem.")
                    if result:
                        print(f"Recommended action: Replace device {anomaly.source}.")
                        self.net_desc.toggle_status()
                        break
                    executed[('replace_dev', new_device)] = result
                if len(l1_replacedev_candidates) == 0:
                    ## No more replace device candidates, don't put back in queue
                    continue
            else: raise RuntimeError(f"Unknown troubleshooting action {action_name}")
            heapq.heappush(priority_queue, (action_acc_cost + action_cost, action_cost, action_name))


class UC1AnomalyTrigger(TriggeringSystem):
    """ Triggering system that carries the input description of the UC1 anomaly. 

            In a deployed production version this would be called with the problem information (not UC specific)
        and have the ability to operate on abstraction layers, making the translation of the anomaly into these layers.
    """

    def __init__(self, network: NetworkDescription) -> None:
        self.user = 'Jane'
        self.user_device = 'Laptop1'
        self.output_device = 'Printer1'
        self.network = network
        print(f"Use Case 1 Anomaly report:")
        print(f"--> User reporting: {self.user}")
        print(f"--> User device: {self.user_device}")
        print(f"--> User device unable to use use output device {self.output_device}")

    def collect(self) -> UC1Anomaly:
        self.network.toggle_status()
        ## Extract subgraph of Lstar and L0 with anomalies
        broken_lstar = self.network.lstar.graph.subgraph([self.user, self.output_device])
        broken_l0 = self.network.l0.graph.subgraph([self.user_device, self.output_device])
        ## Create Anomaly Description object
        #   Compose it with the known broken parts of lstar and l0
        return UC1Anomaly(broken_lstar, broken_l0, self.user_device, self.output_device)
        

def main(args: List[str]) -> None:
    ## TODO: CLI Args processing
    ## Initial generic understanding of networking.
    l2_ontology = __create_uc1_l2_ontology()
    nx.write_gpickle(l2_ontology, 'initial_l2_memory.gpkl')
    ## Get L0 for use case 1
    print("Collecting L0 translation from data...")
    time.sleep(1)
    l0 = create_default_uc1_l0()
    nx.write_gpickle(l0.graph, 'initial_l0.gpkl')
    ## Combine l0 and l2 long term memory to build initial l1
    print("Generating L1 from L0 and long term L2 memory...")
    time.sleep(1)
    l1 = generate_l1(l0, l2_ontology)
    nx.write_gpickle(l1, 'l1.gpkl')
    ## Generate initial L* state, with working network
    users = [concept for concept, l2_abstraction in l0.tag_dict.items() if l2_abstraction == 'User']
    lstar = Lstar(users)
    ## Bundle concept layers into single NetworkDescription object
    network_description = NetworkDescription(l0,l1,l2_ontology,lstar)
    ## Troubleshooting agent
    agent = UC1TroubleshootingAgent(network_description)
    nx.write_gpickle(agent.l2_expertise, 'l2_troubleshooting_expertise.gpkl')
    ## Combine all layers into single Network Description and create triggering system for UC1, registering the agent. Trigger UC1 defect and repair
    anomaly_trigger = UC1AnomalyTrigger(network_description)
    print(f"Send anomaly information...")
    time.sleep(1)
    anomaly = anomaly_trigger.collect()
    ## Call troubleshooting agent to repair anomaly description
    agent.repair(anomaly)
    if network_description.status == NetworkStatus.WORKING: print("\nAnomaly troubleshooted successfully!")
    else: print("\nTroubleshooting agent was unable to repair network.")

