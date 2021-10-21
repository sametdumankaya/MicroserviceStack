from dfre4net2.DFRE_KG import DFRE_KG
import pandasql as pdsql
import pandas as pd
import networkx as nx

def sql_query_KG(kg:DFRE_KG(),sql:str) ->DFRE_KG():
    #TODO: replace print with logging.info 
    print(f"Querying DFRE KG for sql= {sql}")
    #Constructing relations and concepts dictionaries
    #Relations are represented as with source and target
    concepts=pd.DataFrame()
    relations=pd.DataFrame()
    relations=nx.convert_matrix.to_pandas_edgelist(kg.g)
    concepts =pd.DataFrame.from_dict(kg.g.nodes, orient='index')
    #by default concept names are indexes. resetting the index.
    concepts=concepts.rename_axis(["concepts"])
    concepts=concepts.reset_index()
    if(len(concepts)==0):
        concepts =pd.DataFrame.from_dict(kg.g.nodes)
        concepts.rename(columns={concepts.columns[0]:"concepts"},inplace=True)
    #run the query string
    result = pdsql.sqldf(sql, {**locals(), **globals()})
    #Construct context wrt the query result
    context=[]
    #Check concepts
    if("concepts" in result.columns):
        context=result['concepts'].tolist()
    #check relations. 
    #if result contains relations, networkx edges are minimally defined as (source,target) pairs.
    if(len(result.columns)>=2 and "source" in result.columns and "target" in result.columns):
        context=context+result['source'].tolist()+result['target'].tolist()
    #remove doublicates
    context=list(set(context))
    seed_context=kg.g.subgraph(context)
    #Query result as knowledge graph
    result_KG=DFRE_KG(graph=seed_context)
    return result_KG

def sql_query_KG_concepts_pd(kg:DFRE_KG(),sql:str) ->pd.DataFrame():
    #TODO: replace print with logging.info 
    print(f"Querying DFRE KG for sql= {sql}")
    #Constructing relations and concepts dictionaries
    #Relations are represented as with source and target
    concepts=pd.DataFrame()
    relations=pd.DataFrame()
    relations=nx.convert_matrix.to_pandas_edgelist(kg.g)
    concepts =pd.DataFrame.from_dict(kg.g.nodes, orient='index')
    #by default concept names are indexes. resetting the index.
    concepts=concepts.rename_axis(["concepts"])
    concepts=concepts.reset_index()
    if(len(concepts)==0):
        concepts =pd.DataFrame.from_dict(kg.g.nodes)
        concepts.rename(columns={concepts.columns[0]:"concepts"},inplace=True)
    #run the query string
    result = pdsql.sqldf(sql, {**locals(), **globals()})
    #Construct context wrt the query result
    return result

def sql_query_KG_relations_pd(kg:DFRE_KG(),sql:str) ->pd.DataFrame():
    relations=pd.DataFrame()
    relations=nx.convert_matrix.to_pandas_edgelist(kg.g)
    result = pdsql.sqldf(sql, {**locals(), **globals()})
    return result
    
def cleanGraphSymbols(G:nx.Graph,symbols:list=None)->nx.Graph():
    """This function cleans symbols from graph attributes for visualization."""
    outp=nx.Graph(G)
    if(symbols is None): symbols=['[',']','nan']
    for node in list(outp.nodes(data=True)):
        name=node[0]
        attributes=outp.nodes[name]
        for key,val in attributes.items():
            for s in symbols:
                if(s in str(val)):
                    outp.nodes[name][key]=str(outp.nodes[name][key]).replace(s,'')
    return outp     
        
