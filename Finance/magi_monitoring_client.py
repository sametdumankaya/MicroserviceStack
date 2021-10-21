import requests
import json


class MagiMonitoringClient:
    def __init__(self, url):
        self.url = url

    def construct_metamodel_from_ts_output(self, output_name: str):


        response = requests.post(f'{self.url}/construct_metamodel_from_ts_output',
                                 json={
                                     "output_name": output_name
                                 })
        rtrn = json.loads(response.content)
        return rtrn['result']


