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

counter = 0
while True:
    key = "poc_data"
    # all green, then edit values wrt time
    queue_entry = {
        x: random.randint(0, 29) for x in keys
    }
    queue_entry["message"] = "Systems nominal"

    if 10 < counter < 30:
        queue_entry["dr01"] = random.randint(61, 99)
        queue_entry["dr03"] = random.randint(31, 59)
        queue_entry["message"] = "There are errors in dr01 and dr03."

    redis_client.hset(key, None, None, queue_entry)
    time.sleep(1)
    counter += 1
    if counter == 40:
        break
