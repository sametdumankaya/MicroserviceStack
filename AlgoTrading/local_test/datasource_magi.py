import requests
import redis
from redistimeseries.client import Client

input_redis = redis.Redis(host="localhost", port=6381, decode_responses=True)
input_rts = Client(input_redis)
info = input_rts.info("rts1:01:symbol:GOOG:volume")

response_datasource = requests.post("http://localhost:8000/start_historical_trading_data_source/", json={
    "input_redis_port": 6381,
    "news_port": 8007,
    "output_redis_port": 6390,
    "sample_rate_msec": 1000,
    "price_label": "ACTIVE_PRICE",
    "volume_label": "ACTIVE_VOLUME",
    "start_timestamp": info.first_time_stamp,
    "end_timestamp": info.lastTimeStamp,
    "bucket_size_msec": 1000,
    "wait_time_msec": 0
}).json()

print(response_datasource)
