import networkx as nx
import pandas as pd
import os
from matplotlib import pyplot as plt

def extract_edge_idx(G):
    edges=list(G.edges)
    nodes=list(G.nodes)
    new_edge_list = [None]
    j=0
    for i in range(len(edges)):
        if edges[i][2]==0:
            new_edge_list.append(i)
            idx1 = nodes.index(edges[i][0])
            idx2 = nodes.index(edges[i][1])
            new_edge_list[j] = (idx1+1,idx2+1,1)
            j=j+1
    return new_edge_list

def norm_cost(graph_name):
    cost=pd.read_csv(graph_name+'_VoG_output',header=None,delim_whitespace=True)
    x=cost[1]
    normalized_x=((x-x.min())/(x.max()-x.min()))*100
    cost.insert(2,2,normalized_x)
    return cost

def sum2graph(graph_name,n):
    
    '''
    Inputs : graph_name : Name of the graph being summarized 'i.e. alertstorm'
             n : If focused on the first # of nodes 
             oG : The original networkx graph ... returned with VoG attributes  
             
    This code creates a L2 VoG graph used to visualize the structures found in L1 
    
    Additionally writes the original L1 graph with VoG cost attributes for top the top 300 structures. 
    '''
    
    # Initialize Graph Foundation
    G=nx.Graph()
    G.add_node('VoG')
    G.add_node('Bipartite')
    G.add_node('Cliques')
    G.add_node('Stars')
    G.add_node('Summary')
    G.add_node('Top50')
    G.add_node('Top100')
    G.add_node('Top200')
    G.add_node('Top300')
    G.add_edge('VoG','Bipartite')
    G.add_edge('VoG','Cliques')
    G.add_edge('VoG','Stars')
    G.add_edge('VoG','Summary')
    G.add_edge('Summary','Top50')
    G.add_edge('Summary','Top100')
    G.add_edge('Summary','Top200')
    G.add_edge('Summary','Top300')
    
    oG = nx.read_graphml(r'C:\Users\Adam Lawrence.DESKTOP-C98S9IM\VoG_Graph_Summarization\DATA\AlertStrom_HNMTopology_WithAlerts.graphml')
    oG_nodes=list(oG.nodes)
    cost= norm_cost('alertstorm')
    l=len(oG.nodes)
    cost_KG=[0]*l
    
    
    # Read in the data
    raw = open(path+'\DATA\\'+graph_name+'_orderedALL.model', "r")
    structure_list = raw.read().split('\n') 
    
    rank50=[4,5,7,11,12,13,15,16,18,19,20,21,22,23,25,26,27,29,30,31,32,34,35,36,37,38,41,42,43,44,46,47,49]
    rank100=[4,5,7,11,12,13,15,16,18,19,20,21,22,23,25,26,27,29,30,31,32,34,35,36,37,38,41,42,43,44,46,47,49,51,54,55,58,60,61,63,64,65,67,68,69,70,71,72,74,76,77,78,81,82,83,85,86,87,88,89,92,93,94,95,96,97,100]
    rank200=[4,5,7,11,12,13,15,16,18,19,20,21,22,23,25,26,27,29,30,31,32,34,35,36,37,38,41,42,43,44,46,47,49,51,54,55,58,60,61,63,64,65,67,68,69,70,71,72,74,76,77,78,81,82,83,85,86,87,88,89,92,93,94,95,96,97,100,101,102,104,105,106,107,108,110,111,112,113,114,115,129,142,143,144,145,146,147,148,149,151,165,166,167,168,169,170,171,172,173,174,175,189,190,191,192,193,194,195,196,197,199,200]
    rank300=[4,5,7,11,12,13,15,16,18,19,20,21,22,23,25,26,27,29,30,31,32,34,35,36,37,38,41,42,43,44,46,47,49,51,54,55,58,60,61,63,64,65,67,68,69,70,71,72,74,76,77,78,81,82,83,85,86,87,88,89,92,93,94,95,96,97,100,101,102,104,105,106,107,108,110,111,112,113,114,115,129,142,143,144,145,146,147,148,149,151,165,166,167,168,169,170,171,172,173,174,175,189,190,191,192,193,194,195,196,197,199,200,201,202,203,204,205,206,207,273,274,275,276,277,278,281,285,287,288,290,291,293,299]
    
    
    for i in range(n):
        
        G.add_node(i)
        
        if i in rank50:
            G.add_edge(i,'Top50')
        if i in rank100:
            G.add_edge(i,'Top100')
        if i in rank200:
            G.add_edge(i,'Top200')
        if i in rank300:
            G.add_edge(i,'Top300')
            cost_id=cost.index[cost[0] == i].tolist()
            cost_id=cost_id[0]
        
        structure = structure_list[i]
        structure = structure.split(',')
        node1 = structure[0]
        node1_str = node1[3:]
        node2_str = structure[1]
        a_list = node1_str.split()
        b_list = node2_str.split()
        a_map_object = map(int, a_list)
        b_map_object = map(int, b_list)
        
        struct_type = node1[:2] # Type of structure of row i 
        node1_int = list(a_map_object) # set1 of nb , hub of st
        node2_int = list(b_map_object) # set2 of nb , spokes of st

        if struct_type=='nb':
            G.add_edge(i,'Bipartite')
            G.add_node('set1_'+str(i))
            G.add_node('set2_'+str(i))
            G.add_edge('set1_'+str(i),i)
            G.add_edge('set2_'+str(i),i)

            for j in range(len(node1_int)):

                str1=str(node1_int[j])
                idx = node1_int[j]
                G.add_node('L1_'+str1)
                G.add_edge('L1_'+str1,'set1_'+str(i))
                
                if i in rank300:
                    cost_KG[idx] = int(cost[2][cost_id])
                
            for j in range(len(node2_int)):

                str2=str(node2_int[j])
                idx = node2_int[j]
                G.add_node('L1_'+str2)
                G.add_edge('L1_'+str2,'set2_'+str(i))
                
                if i in rank300:
                    cost_KG[idx] = int(cost[2][cost_id])   
                
        if struct_type=='st':
            
            G.add_edge(i,'Stars')
            G.add_node('hub_'+str(i))
            G.add_node('spokes_'+str(i))
            G.add_edge('hub_'+str(i),i)
            G.add_edge('spokes_'+str(i),i)

            for j in range(len(node1_int)):

                str1=str(node1_int[j])
                idx = node1_int[j]
                G.add_node('L1_'+str1)
                G.add_edge('L1_'+str1,'hub_'+str(i))
                                         
                if i in rank300:
                    cost_KG[idx] = int(cost[2][cost_id])

            for j in range(len(node2_int)):

                str2=str(node2_int[j])
                idx = node2_int[j]
                G.add_node('L1_'+str2)
                G.add_edge('L1_'+str2,'spokes_'+str(i))
                                         
                if i in rank300:
                    cost_KG[idx] = int(cost[2][cost_id])
        
    
    zipbObj = zip(oG_nodes,cost_KG)
    oG_cost = dict(zipbObj)
    nx.set_node_attributes(oG, oG_cost, 'norm_cost')
    
    nx.write_graphml(G,graph_name+'L2_VoGstructure_graph.graphml')
    nx.write_graphml(oG,graph_name+'L1_VoGattributes_graph.graphml')
    
    return G , cost_KG , oG_nodes

