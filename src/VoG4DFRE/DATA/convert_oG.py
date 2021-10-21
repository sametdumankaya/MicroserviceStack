import networkx as nx
import os
import pandas as pd
import VoG_util as vog
'''
This creates a .out file that the structure discovery phase uses.
Converts a nx graph into a coordanite list of node-edge relationships.

0 : 1 , 1000 
1 : 2 , 1000 
  : 
  :
n : n+1 , m 

'''

# This is hardcoded right now for AlertStorm H&M , needs to be updated for user input 
oG = nx.read_graphml('AlertStrom_HNMTopology_WithAlerts.graphml')

new_edge_list = vog.extract_edge_idx(oG)

n=len(new_edge_list)
n=n-1
index=range(0,n)
df = pd.DataFrame(index=range(n),columns=[0,1,2])
for i in range(n):
    df[0][i] =new_edge_list[i][0]
    df[1][i] =new_edge_list[i][1]
    df[2][i] =new_edge_list[i][2]


df.to_csv('alertstorm.out',header=None,index=False)
