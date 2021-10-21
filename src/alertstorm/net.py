import argparse
import networkx as nx
import requests as req
from typing import List

from dfre4net.layer import L1, L2

class HttpReceiver:
    
    def __init__(self, protocol: str, host: str, route: str, port: int) -> None:
        self.proto = protocol
        self.host = host
        self.route = route
        self.port = port 


def config_from_cli(cli_options: argparse.Namespace) -> HttpReceiver:
    return HttpReceiver(
        protocol=cli_options.proto, 
        host=cli_options.host, 
        route=cli_options.route, 
        port=cli_options.port
    )

def pack(alerts: List[str], l1: L1, l2: L2) -> list:
    graph = l1.kg.g
    json_obj = []
    alerts_without_l2_mapping_path = 0
    for alert in alerts:
        alert_node = graph.nodes[alert]
        alert_obj = {
            'title': alert_node['title'],
            'alert_id': alert_node['alert_id'],
            'issue_id': alert_node['issue_id'],
            'problem_id': alert_node['problem_id'],
            'alertstorm_severity': alert_node['severity'],
            'date': alert_node['date'],
            'dfre_severity': alert_node['dfre_severity'],
            'dfre_severity_strat': 'avg'
        }
        alert_intension = l1.intension[alert]
        if type(alert_intension) == str: alert_intension = [ alert_intension ]
        paths = []
        for intension_instance in alert_intension:
            path = '.'.join(nx.shortest_path(l2.stm.g,'Alertstorm',intension_instance))
            if len(path) > 0: paths.append(path)
        if len(paths) == 0: alerts_without_l2_mapping_path += 1 
        alert_obj['l2_map_paths'] = paths
        json_obj.append(alert_obj)
    if( alerts_without_l2_mapping_path>0 ):
        print(f"WARNING: Packing {alerts_without_l2_mapping_path} alerts without an L2 mapping path.")
    return json_obj

def send(json_obj: list, config: HttpReceiver) -> None:
    url = config.proto + '://' + config.host + ':' + str(config.port) + config.route
    req.post(url, json=json_obj)
