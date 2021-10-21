import pickle

import redis

client = redis.Redis(port=51969)

data = client.lrange("NewsIndustry", -100, 110)
qq = client.llen("NewsIndustry")
items = []
for item in data:
    items.append(pickle.loads(item))
print("q")