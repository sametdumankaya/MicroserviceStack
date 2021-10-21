from redis import Redis
import random
import datetime
import time
from redistimeseries.client import Client

redis_client = Redis(host="localhost", port=6379, decode_responses=True)
rts = Client(redis_client)

keys = [f"test{x+1}" for x in range(3)]

try:
    for key in keys:
        rts.create(key)
except:
    for key in keys:
        redis_client.delete(key)
        rts.create(key)

while True:
    timestamp = int(datetime.datetime.now().timestamp()) * 1000
    rts.madd([(key, timestamp, random.randint(1, 100)) for key in keys])
    time.sleep(1)
