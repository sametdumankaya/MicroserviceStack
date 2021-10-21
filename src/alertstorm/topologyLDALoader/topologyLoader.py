import networkx as nx
import pandas as pd
import numpy as np

def loadTopologyFromBorg(devices:list, connections:list)->nx.MultiGraph:
    """This function creates topology from csv files produced by BORG, ISIS and BGP systems and returns networkx graph"""
    """Arguments:
    devices: list of two string csv files containing device-names 
    connections: list of two string csv files containing connections """
    
    """Returned graph can be disconnected. Use
    largest_cc = max(nx.connected_components(G), key=len)
    largest_subgraph=G.subgraph(list(largest_cc)) to get the largest connected subgraph"""
    
    G= nx.MultiGraph()
    #Read devices
    d1 = pd.read_csv(devices[0])
    d2= pd.read_csv(devices[1])
    merged_dev=pd.merge(d1,d2[['Device', 'Tag', 'VRF', 'Net', 'Network' ]],on='Device', how='outer')
    #Read connections
    c1=pd.read_csv(connections[0])
    c2=pd.read_csv("BGP-HANDM.csv")
    #Clean nan in devices and connections
    merged_dev = merged_dev.replace(np.nan, '', regex=True)
    c1 = c1.replace(np.nan, '', regex=True)
    c2 = c2.replace(np.nan, '', regex=True)
    #Scan all devices and add nodes
    for i, dev in merged_dev.iterrows():
        name=dev['Device']
        tmp_vendor=dev['Vendor']
        tmp_os=dev['OS']
        tmp_os_version=dev['OS Version']
        tmp_model=dev['Model']
        tmp_management_address=dev['Management Address']
        tmp_source=dev['Source']
        tmp_command_files=dev['Command Files'] 
        tmp_tag=dev['Tag']  
        tmp_vrf=dev['VRF']  
        tmp_net=dev['Net'] 
        tmp_network=dev['Network'] 
        G.add_node(name,vendor=tmp_vendor, os=tmp_os, os_version=tmp_os_version,model=tmp_model,management_address=tmp_management_address, source=tmp_source, \
                   command_files=tmp_command_files, tag=tmp_tag, vrf=tmp_vrf, net=tmp_net, network=tmp_network)
    #Scan all connections and add edges
    for i,conn in c1.iterrows():
        src_name=conn['Source Hostname']
        target_name=conn['Target Hostname']
        src_interface =conn['Source Interface']
        src_interface_ipv4=conn['Source Interface IPv4']
        trg_interface =conn['Target Interface']
        trg_interface_ipv4=conn['Target Interface IPv4']
        G.add_edge(src_name,target_name,\
                   source_interface=src_interface, source_IP=src_interface_ipv4, \
                   target_interface=trg_interface, target_ip=trg_interface_ipv4)
    for i,conn in c2.iterrows():
        src_name=conn['Device']
        target_name=conn['NeighborName']
        trg_interface_ipv4=conn['NeighborIP']    
        G.add_edge(src_name,target_name,target_ip=trg_interface_ipv4)
    
    return G
if __name__ == "__main__":
    G=nx.Graph()
    customer="HnM"
    devices=[customer+"/"+'Devices-HANDM.csv',customer+"/"+'ISIS-HANDM.csv']
    connections=[customer+"/"+'Connections-HANDM.csv', customer+"/"+'BGP-HANDM.csv']
    G=loadTopologyFromBorg(devices,connections)
    largest_cc = max(nx.connected_components(G), key=len)
    largest_subgraph=G.subgraph(list(largest_cc))
    nx.write_graphml(largest_subgraph,'LargestCC_topologyBorg.graphml')