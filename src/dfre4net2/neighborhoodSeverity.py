import networkx as nx
import pandas as pd

def getNeighborSeverity(G:nx.Graph, hop_distance:int,attrib_name:str,isNormalize:bool)->pd.DataFrame:
    """Thus function sums the value of attrib_name per device and its neighbors within hop_distance. 
    If isNormalize True, it returns normalized dataframe."""
    G=nx.Graph(G)
    df=pd.DataFrame(columns=['node','dfre_severity'])
    for n in G.nodes(data=True):
        if(attrib_name in n[1]):
            if(float(n[1][attrib_name])>0):
                #Ego graph with a radius
                sub_graph=nx.ego_graph(G, n[0],radius=hop_distance)
                neighbor_sum=getNeighborSum(sub_graph,attrib_name)
                df.loc[len(df)]=[n[0],neighbor_sum]

    df = df.set_index('node')
    if(len(df)>0 and isNormalize):
        df=(df/df.max())
    return df
        
def getNeighborSum(sub_graph:nx.Graph, attrib_name:str)->float:
    """Thus function sums all values of a given attrib_name for entire graph"""
    total=0
    for n in sub_graph.nodes(data=True):
        if(attrib_name in n[1]):
            total=total+float(n[1][attrib_name])
    return total

if __name__ == "__main__":
    hop_distance=1
    attrib_name='problem_count'
    isNormalize=False
    G=nx.read_graphml('LargestCC_topologyBorgWithAlerts.graphml')
    neighborSeverity=getNeighborSeverity(G,hop_distance,attrib_name,isNormalize)