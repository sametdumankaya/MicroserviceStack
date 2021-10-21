from redis import Redis
import random
import time
import json

redis_client = Redis(host="localhost", port=6379, decode_responses=True)

keys = ["engine", "room", "boiler", "room2", "hutchCeiling", "turboGen", "crewClub", "poop", "bedroom"]
while True:
    key = "poc_data"
    queue_entry = {
        x: json.dumps({"value": random.randint(0, 100), "threshold": random.randint(0, 100)}) for x in keys

    }
    redis_client.hmset(key, queue_entry)
    time.sleep(1)
