# Visualization API

This repository contains the visualization api code. It exposes an interface to create grafana dashboards programmatically. 

## Accessing Grafana
Visit http://localhost:3000 to browse Grafana.


## API Methods

### create_timeseries_graphs
Creates a dashboard to visualize specified time series that stored in Redis.
#### Parameters
* time_series_info_list: names of the time series
* time_range_start: start timestamp of the time series in milliseconds
* time_range_end: end timestamp of the time series in milliseconds

### create_streaming_timeseries_graphs
Creates a dashboard to visualize specified STREAMING time series that stored in Redis.
#### Parameters
* streaming_time_series_info_list: names of the STREAMING time series
* last_minutes_count: number indicating how many last minutes to show
* refresh_interval: frequency of refreshing the table

### add_annotations
Adds annotations to panels in Grafana dashboard
#### Parameters
* dashboard_id: id of the dashboard
* annotations: list of annotations, each specified with timestamp and description 

### create_video_dashboard
Creates a dashboard with a video panel in it.
#### Parameters
* video_url: URL of the video
* dashboard_title: title of the dashboard

## Sample Requests
Sample request bodies (JSON) can be found under sample_request folder for each API Method.