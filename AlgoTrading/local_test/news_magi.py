import requests
from datetime import datetime

r = requests.post("http://localhost:8007/getNewsFromRedisBetweenDates/", json={
    "startDate": datetime.fromtimestamp(1629158400000 / 1000).strftime("%Y-%m-%d %H:%M:%S.%f"),
    "endDate": datetime.fromtimestamp(1629244800000 / 1000).strftime("%Y-%m-%d %H:%M:%S.%f")
}).json()
print("a")



