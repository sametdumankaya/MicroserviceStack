from redis import Redis
import random
import time

redis_client = Redis(host="localhost", port=6379, decode_responses=True)

keys = ["dr01",
        "leaf1", "leaf2", "leaf3", "leaf4",
        "spine1", "spine2", "spine3", "spine6",
        "dr03",
        "leaf5", "leaf6", "leaf7", "leaf8",
        "dr02"]

while True:
    key = "poc_data"
    queue_entry = {
        x: random.randint(0, 100) for x in keys
    }

    queue_entry["message"] = "Systems nominal"
    redis_client.hset(key, None, None, queue_entry)
    time.sleep(1)
