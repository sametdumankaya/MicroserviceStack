import requests


class VisApiClient:
    def __init__(self, url):
        self.url = url

    def create_streaming_timeseries_graphs(self, time_series_names: list, title: str, last_minutes_count: int,
                                           refresh_interval: str):
        response = requests.post(f'{self.url}/create_streaming_timeseries_graphs',
                                 json={
                                     "streaming_time_series_info_list": [
                                         {
                                             "time_series_name": time_series_name
                                         } for time_series_name in time_series_names
                                     ],
                                     "title": title,
                                     "last_minutes_count": last_minutes_count,
                                     "refresh_interval": refresh_interval,
                                     "datasource": None
                                 }).json()
        return response["created_streaming_dashboard_id"]
