import json
import urllib
from datetime import datetime
import requests


class MSigClient:
    def __init__(self, url):
        self.url = url

    def getNewsFromRedis(self, count: int, date: str):
        response = requests.post(f'{self.url}/getNewsFromRedis',
                                 json={
                                     "count": count,
                                     "date": date
                                 }).json()
        return response



