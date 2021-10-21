from redis import Redis
import random
import time
import json
import sys
import argparse

def get_cli_parser() -> argparse.ArgumentParser:
    cli_parser = argparse.ArgumentParser(add_help=False)
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
        help='Port for redis'
    )
    cli_parser.add_argument(
        '--eventName',
        type=str,
        default="blackhole",
        help='Name of the demo event to be injected'
    )
    cli_parser.add_argument(
        '--devices',
        nargs="*",
        type=str,
        default=["leaf3"],
        help='Device names affected by this event'
    )
    cli_parser.add_argument(
        '--durations',
        nargs="*",
        type=int,
        default=[10,30,20],
        help='Durations for event the event injection. 1) wait for the injection 2) wait for the end of the injection 3) wait for the end of the experiment'
    )
    return cli_parser
def simulateEvent(topology:dict, redishost:str,redisport:int,eventName:str,impacted_devices:list,durations:list)->None:
    rooms=list(topology.keys())
    devices=list(topology.values())
    most_impacted_devices={"blackhole":["leaf3","dr01"],"portshutdown":["dr01","dr03"]}
    #bhole="leaf3"
    #psdown= ["leaf1","spine2"]
    redis_client=Redis(host=redishost,port=redisport,decode_responses=True)
    if not redis_client.ping():
        print("Redis is not accessible")
        return
    
    #push everything as normal:
    redis_queue_html="poc_data_html"
    queue_rooms = {
                        x: json.dumps({"value": random.randint(0, 49), "threshold": 50}) for x in rooms

                }
    redis_client.hmset(redis_queue_html, queue_rooms)
    
    redis_queue_grafana="poc_data"
    for d in devices:
        queue_devices = {
        x: random.randint(0, 49) for x in devices
        }
    queue_devices["message"] = "Systems nominal"
    redis_client.hset(redis_queue_grafana, None, None, queue_devices)
    
    time.sleep(durations[0]) 
    print("Injecting event:",eventName)
    if eventName=="blackhole":
       for r, d in topology.items():
           if most_impacted_devices["blackhole"][0] in d:
               queue_rooms[r]= random.randint(80, 100)
               queue_devices[r]= random.randint(80, 100)
               queue_devices["message"] = "Anomaly detected in "+impacted_devices[0]
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
           if most_impacted_devices["blackhole"][1] in d:
               queue_rooms[r]= random.randint(51, 79)
               queue_devices[r]= random.randint(51, 79)
               queue_devices["message"] = "Anomaly detected in "+impacted_devices[0]
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
       time.sleep(durations[1])
       
       #Recover
       print("Ending injection:",eventName)
       for r, d in topology.items():
           if most_impacted_devices["blackhole"][0] in d:
               queue_rooms[r]= random.randint(0, 49)
               queue_devices[r]= random.randint(0, 49)
               queue_devices["message"] = "Systems nominal"
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
           if most_impacted_devices["blackhole"][1] in d:
               queue_rooms[r]= random.randint(0, 49)
               queue_devices[r]= random.randint(0, 49)
               queue_devices["message"] = "Systems nominal"
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
        
    elif eventName=="portshutdown":
       for r, d in topology.items():
           if most_impacted_devices["portshutdown"][0] in d:
               queue_rooms[r]= random.randint(80, 100)
               queue_devices[r]= random.randint(80, 100)
               queue_devices["message"] = "Anomaly detected in "+impacted_devices[0]
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
           if most_impacted_devices["portshutdown"][1] in d:
               queue_rooms[r]= random.randint(51, 79)
               queue_devices[r]= random.randint(51, 79)
               queue_devices["message"] = "Anomaly detected in "+impacted_devices[0]
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
       time.sleep(durations[1])
       
       #Recover
       print("Ending injection:",eventName)
       for r, d in topology.items():
           if most_impacted_devices["portshutdown"][0] in d:
               queue_rooms[r]= random.randint(0, 49)
               queue_devices[r]= random.randint(0, 49)
               queue_devices["message"] = "Systems nominal"
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
           if most_impacted_devices["portshutdown"][1] in d:
               queue_rooms[r]= random.randint(0, 49)
               queue_devices[r]= random.randint(0, 49)
               queue_devices["message"] = "Systems nominal"
               redis_client.hmset(redis_queue_html, queue_rooms) 
               redis_client.hset(redis_queue_grafana, None, None, queue_devices)
    else:
        print("Only the following eventnames are implemented for simulation: blackhole, portshutdown")
    time.sleep(durations[2])
    print("Ending the experiment...")
    return
if __name__ == '__main__':
    topology={"B1":["rswB1"],"B2":[],"B3":["leaf5","leaf6","leaf7","leaf8","sswB3","dr03"],
              "B4":["spine1","spine2","spine3","spine4","spine5","spine6","dr02"],
              "B5":["leaf1","leaf2","leaf3","leaf4"],"B6":["rswB6","dr01"],
              "A1":[],"A2":[],"A3":[],"A4":["rswA4A"],"A5":["rswA5A"],"A6":["rswA6A"]}
    cli_parser = get_cli_parser()
    cli_options = cli_parser.parse_args(sys.argv[1:])
    print("Initiating event injector...")
    simulateEvent(topology,cli_options.redishost, cli_options.redisport, str.lower(cli_options.eventName), cli_options.devices, cli_options.durations)
    #blackhole: leaf3
    #portshutdown: leaf1,spine2
    
    
    
    
    
    
    
    
    
    
    