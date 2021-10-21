import networkx as nx
import pickle
from pathlib import Path
import os,sys
sys.path.append(os.path.dirname(Path(os.path.abspath(__file__)).parent))
from dfre4net2.DFRE_Agent import DFRE_Agent
from dfre4net2.task import Task, Priority
import argparse
from dfre4net2.query_KG import sql_query_KG_concepts_pd
import uuid
from dfre4net2.DFRE_KG import DFRE_KG, merge_KG
import dfre4net2.layer as layer
import redis
import ctypes
from typing import List
import argparse 

USE_CASE_ID="timeseries"


def get_cli_parser() -> argparse.ArgumentParser:
    cli_parser = argparse.ArgumentParser(
        prog=sys.argv[0]+' '+USE_CASE_ID,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )
    ## redishost parameter
    cli_parser.add_argument(
        '--redishost',
        type=str,
        default='localhost',
        help='Host address for redis.'
    )
    ## redisport parameter
    cli_parser.add_argument(
        '--redisport',
        type=int,
        default=6379,
        help='Port number for redis'
    )
    
    return cli_parser

def main(args: List[str]):

    # Send to tmux session
    print("\n### TASK MANAGEMENT AGENT ###\n")
    #Create task management
    tid=str(uuid.uuid4())
    aid=str(uuid.uuid4())
    t=Task(description='Task Management',task_id=tid,requester_agent_id=aid,executer_agent_id=aid,priority=Priority.CRITICAL)
    #Load task management script
    fname='L2tasks.dfrescr'
    #DIR = Path(os.getcwd())
    DIR = Path(os.path.abspath('__file__')).parent
    task_ltm_file = DIR / Path('./timeseries/L2script')/fname
    #Create task management agent with ltm
    print('Initializing a DFRE Agent as Task Management Agent...',task_ltm_file)
    taskManagementAgent=DFRE_Agent(agent_id=aid,task=t,l2=layer.L2(longterm_kg=DFRE_KG(task_ltm_file)))
    #task data is added as binary. pickle.loads needed to read it back.
    concept=[(t.task_id, {"data":str(pickle.dumps(t))})]
    taskManagementAgent.ingestL0(concept)
    taskManagementAgent.ingestL1(concept)
    #l1 intension and l2 extension construction
    mapping_clue=str(t.priority).split('.')[1]
    interlayer_mapping=taskManagementAgent.l2.map_intension(t.task_id,mapping_clue)
    #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
    taskManagementAgent.l1.add_intension(interlayer_mapping)
    #generate extension map from intension
    taskManagementAgent.l2.add_extension(interlayer_mapping)
    cli_parser = get_cli_parser()
    cli_options = cli_parser.parse_args(args)
    global r
    r = redis.Redis(host=cli_options.redishost,port=cli_options.redisport, db=0)
    ########TASK LOOP
    #infinite task management loop until management task is set to complete
    print('Task Management Agent: Listening to task request channel...')
    while not taskManagementAgent.task.isTaskComplete:
        x=r.lpop("Task Manager")    
        if(x is not None):
            try:
                new_task=pickle.loads(x)
                print("Task Management Agent: New task received:", new_task.description, "Requesting agent:", new_task.requester_agent_id)
                print("Task Management Agent: Ingesting new task request into DFRE KB...")
                new_tid=new_task.task_id
                new_concept=[(new_tid, {"data":str(pickle.dumps(new_task))})]
                #ingest new task into internal LoA
                taskManagementAgent.ingestL0(new_concept)
                taskManagementAgent.ingestL1(new_concept)
                #generate interlayer mapping
                mapping_clue=str(new_task.priority).split('.')[1]
                interlayer_mapping=taskManagementAgent.l2.map_intension(new_task.task_id,mapping_clue)
                #interlayer_mapping is in the form of {l1_concept_name:l2_concept_name}. one-to-one
                taskManagementAgent.l1.add_intension(interlayer_mapping)
                #generate extension map from intension
                taskManagementAgent.l2.add_extension(interlayer_mapping)
                #create and execute new task
                new_data=pickle.loads(new_task.data)                
                print("Task Management Agent: Executing", str(new_task.process.__name__), "on data type", str(type(new_data)).split('\'')[1],'...')
                ###############################
                ###Make task process call an asynchronous process 
                finished_task_id,result=new_task.process(new_task)
                print("\n### TASK MANAGEMENT AGENT ###\n")
                ##update finished concept
                print('Task Management Agent:',new_task.description, "task finished. Updating DFRE KG...")
                print('Task Management Agent: killing',new_task.description,'Agent')
                taskManagementAgent.l1._shortterm_knowledge.update_concept_value(finished_task_id,"isTaskComplete",True)
                ###Send the result to requesting agent on REDIS
                print("Task Management Agent: Putting finished task: ",finished_task_id,"and the resulting DFRE KG on the bus for the requester agent:",new_task.requester_agent_id,'...')
                r.set(new_task.requester_agent_id,pickle.dumps(result))
                nx.write_graphml(taskManagementAgent.generate_extension_map_network(),'taskManagementAgentL2Extension.graphml',prettyprint=True, infer_numeric_types=False)
            except Exception as e:
                print(e)
    return
if __name__ == "__main__":
    main(sys.argv[1:])
    
    # import ctypes
    #         graph=ctypes.cast(id_of_other_Graph,ctypes.py_object).value
    #         graph.add_node("AAAAAAA")
            
