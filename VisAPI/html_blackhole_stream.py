from redis import Redis
import random
import time

redis_client = Redis(host="localhost", port=6379, decode_responses=True)

keys = ["Leaf5", "Leaf6", "Leaf7", "Leaf8", "sswB3",
        "rswB1", "Spine2", "Spine3", "Spine4", "Spine5", "Spine6", "dr03", "Spine1", "rswA4A", "rswA5A", "rswA6A",
        "Leaf1", "Leaf2", "Leaf3", "Leaf4", "dr02", "rswB6", "dr01"]

counter = 0
while True:
    key = "poc_data"
    # all green, then edit values wrt time
    queue_entry = {
        x: random.randint(0, 29) for x in keys
    }
    queue_entry["message"] = "Systems nominal"

    if 10 < counter < 30:
        queue_entry["leaf3"] = random.randint(61, 99)
        queue_entry["dr01"] = random.randint(31, 59)
        queue_entry["message"] = "There are errors in leaf3 and dr01."

    redis_client.hset(key, None, None, queue_entry)
    time.sleep(1)
    counter += 1
    if counter == 40:
        break
