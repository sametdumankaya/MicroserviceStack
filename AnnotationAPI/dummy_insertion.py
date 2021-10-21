import json
import os
from redis import Redis
import random
import time
counter = 0

while True:
    try:
        if counter % 10000 == 0:
            print(
                f"Trying to connect redis at host: {os.getenv('output_redis_host', 'localhost')}, port: {int(os.getenv('output_redis_port', 6379))}")
        redis_output_client = Redis(host=os.getenv('output_redis_host', "localhost"),
                                    port=int(os.getenv('output_redis_port', 6379)),
                                    decode_responses=True)

        redis_output_client.ping()
        print("Connected!")
        break
    except:
        if counter % 10000 == 0:
            print("Connection failed. Trying again")
        counter += 1
        continue
keys = ["engine", "room", "boiler", "room2", "hutchCeiling", "turboGen", "crewClub", "poop", "bedroom"]
while True:
    key = "poc_data_html"
    queue_entry = {
        x: json.dumps({"value": random.randint(0, 100), "threshold": random.randint(0, 100)}) for x in keys

     }

    # redis_output_client.hmset(key, queue_entry)

    redis_output_client.xadd(key, queue_entry)
    info =redis_output_client.xinfo_stream(key)
    print(f"last item {redis_output_client.get('news_last_generated_id')}\n")
    redis_output_client.set("news_last_generated_id", info["last-generated-id"])
    print(f"new item {redis_output_client.get('news_last_generated_id')}\n")
    time.sleep(1)