import requests
from time import sleep

while True:
    response = requests.post('http://localhost:8007/financial_timeseries_to_neo4j/',
                                 json={
                                     "data_type": "VOLUME"
                                 }).json()
    print("Sleeping...")
    sleep(600)
