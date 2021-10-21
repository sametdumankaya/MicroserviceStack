from abc import ABC
import dfre4net2.layer as layer
import dfre4net2.task as task
from typing import Optional
from dfre4net2.DFRE_KG import DFRE_KG
import networkx as nx
from py2cytoscape.data.cyrest_client import CyRestClient
from dfre4net2.query_KG import cleanGraphSymbols


from dfre4net2.query_KG import cleanGraphSymbols
class DFRE_Agent(ABC):
    def __init__(self, description:Optional[str]=None,l0:Optional[layer.L0]=None, l1:Optional[layer.L1]=None, 
                 l2:Optional[layer.L2]=None, lstar:Optional[layer.Lstar]=None,
                 agent_id:Optional[str]=None, task:Optional[task.Task]=None,enableCytoscape:Optional[bool]=None) -> None:
        self.l0 = l0
        self.l1 = l1
        self.l2 = l2
        self.lstar=lstar
        if(description is None): self.description=''
        else: self.description=description
        if(l0 is None):
            self.l0=layer.L0(shortterm_kg=DFRE_KG())
        if(l1 is None):
            self.l1=layer.L1(shortterm_kg=DFRE_KG())
        if(l2 is None):
            self.l2=layer.L2(shortterm_kg=DFRE_KG(),longterm_kg=DFRE_KG)
        if(lstar is None):
            self.lstar=layer.Lstar(shortterm_kg=DFRE_KG(),longterm_kg=DFRE_KG)
        self.agent_id=agent_id
        self.task=task
        if(agent_id is not None):
            print(f"DFRE Agent: A new agent created with id: {agent_id}")
        if(enableCytoscape):
            try:
                self.cy = CyRestClient()
            except Exception as e:
                print(e)
    def ingestL0(self,concepts:list):
        self.l0.stm.create_concept(concepts)
    def ingestL1(self,concepts:list):
        self.l1.stm.create_concept(concepts)
    def ingestL2(self,concepts:list):
        self.l2.stm.create_concept(concepts)
    def generate_extension_map_network(self)->nx.MultiDiGraph():
        #Combine KG in different layers for display purpose only
        net=self.l2.stm.g.copy()
        net.add_nodes_from(self.l1.stm.g.nodes(data=True))
        net.add_edges_from(self.l1.stm.g.edges(data=True))
        for l2concept, l1concept_list in self.l2._extension_map.items():
            for l1concept in l1concept_list:
                net.add_edge(l2concept,l1concept)
        net=cleanGraphSymbols(net)
        return net
    def send2Cytoscape(self)->None:
        #Create cytoscape network for the first time
        if(hasattr(self, 'cynetwork')==False):
            self.cynetwork=self.cy.network.create_from_networkx(network=cleanGraphSymbols(nx.compose(self.l2.stm.g,self.l1.kg.g)),name='L2 DFRE KG Extension', collection=self.description.replace(' ',''))
            self.cy.layout.apply('force-directed-cl',network=self.cynetwork)
            style=self.cy.style.create('default')
            self.cy.style.apply(style,network=self.cynetwork)
        else:
        #there is already a cytoscope network initialized.
            cynodes=self.cynetwork.get_node_table()
            cynodes=cynodes[['name','SUID']]        
            cyedges=self.cynetwork.get_edge_table()
            cyedges=cyedges[['source','target']]  
            extensions=self.l2._extension_map
            
            #if(len(extensions)<1): return
            for ext,ext_list in extensions.items():
                edge_list=[]
                src=cynodes[cynodes['name']==str(ext)]['SUID'].values
                if(len(src)>0):src=int(src[0])
                if(type(src)!=int):src=int(self.cynetwork.add_node(ext)[ext])
                for item in ext_list:
                    dest=cynodes[cynodes['name']==item]['SUID'].values
                    if(len(dest)>0):dest=int(dest[0])
                    else:dest= int(self.cynetwork.add_node(item)[item])
                    df_edge_exist= cyedges[(cyedges['source'] == ext)  & (cyedges['target']==item)]
                    if(len(df_edge_exist)>0):
                        break
                    edge_list.append({'source':src,'target':dest})
                if(len(edge_list)>0):
                    try:
                        self.cynetwork.add_edges(edge_list)
                    except Exception as e:
                        print(len(edge_list))
                        print(ext)
                self.cy.layout.apply('force-directed-cl',network=self.cynetwork)
                style=self.cy.style.create('default')
                self.cy.style.apply(style,network=self.cynetwork)
       