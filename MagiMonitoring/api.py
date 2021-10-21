import os
import time
import uuid
from datetime import datetime
from typing import Optional
from zipfile import ZipFile

import apscheduler.jobstores.base
import docker
import pytz
import requests
import uvicorn
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from redis import Redis
from docker.errors import NotFound

import magi_web_utils
from datasource_utils import DatasourceUtils
from metamodel_utils import MetamodelUtils
from misc import get_container_dict, prune_containers, find_free_port
from neo4j_api_client import Neo4jApiClient


class KillContainerRequest(BaseModel):
    container_id: str


class StartContainerRequest(BaseModel):
    redis_host: str
    redis_port: int
    output_redis_host: str
    output_redis_port: int
    from_time: int
    to_time: int
    aggregation_type: str
    bucket_size_msec: int
    num_regimes: int
    ts_freq_threshold: int
    peek_ratio: float
    enablePlotting: bool
    enablePrediction: bool
    enablePercentChange: bool
    window: int
    timeZone: str
    process_period: int
    enableBatch: bool
    miniBatchTimeWindow: int
    miniBatchSize: int
    enableStreaming: bool
    operation_mode: str
    percent_change_event_ratio: float
    percent_change_indicator_ratio: float
    input_filters: str
    output_stream_name: str
    file_url: str
    custom_changepoint_function_name: str
    custom_changepoint_function_script: str
    chow_penalty: int
    model: str
    enableFillMissingDataWithLast: bool
    enableOnlineMonitor: bool
    ts_list: str
    subsequenceLength: int
    windowSize: int
    excl_factor: int
    n_regimes: int
    stream_refresh_rate: int
    percent_change_threshold: float
    percent_window: int
    last_minutes_count: int
    refresh_interval: str
    dashboard_title: str


class ProcessFinanceTimeseriesOutputRequest(BaseModel):
    redis_key: str
    is_infinite: bool = False


class RegisterNewsJobRequest(BaseModel):
    job_start_hour: str = "05"
    job_start_minute: str = "30"


class RegisterTimeSeriesJobRequest(BaseModel):
    job_interval: int = 10
    magi_finance_port = 5000
    input_redis_port: int = 6381
    output_redis_port: int = 6379
    is_historical: bool = False


class DeleteJobRequest(BaseModel):
    job_id: str


class ConstructMetamodelFromTSOutputRequest(BaseModel):
    output_name: str


class GenerateMetaModelRequest(BaseModel):
    redis_key: str


class StartRandomTradingDataSourceRequest(BaseModel):
    sample_rate_msec: int
    stock_count: int
    output_redis_host: str
    output_redis_port: int
    wait_time_msec: int


class StartLiveStreamingTradingDataSourceRequest(BaseModel):
    input_redis_host: str
    input_redis_port: int
    output_redis_host: str
    output_redis_port: int
    sample_rate_msec: int
    price_label: str
    volume_label: str
    bucket_size_msec: int
    wait_time_msec: int


class StartHistoricalTradingDataSourceRequest(BaseModel):
    sample_rate_msec: int
    price_label: str
    volume_label: str
    date: str
    bucket_size_msec: int
    wait_time_msec: int
    ts_job_interval_minutes: Optional[int]


class StartMagiWebRequest(BaseModel):
    magi_web_ui_port: int
    magi_web_mysql_port: int


class KillMagiWebRequest(BaseModel):
    project_name: str


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

counter = 0
while True:
    try:
        if counter % 10000 == 0:
            print(
                f"Trying to connect Mongodb...")
        mongo_client = MongoClient('mongodb://localhost:27017')
        mongo_client.admin.command('ping')
        print("Connected!")
        break
    except:
        if counter % 10000 == 0:
            print("Connection failed. Trying again")
        counter += 1
        continue

stock_backups_path = os.getenv("stock_backups_path", "/home/magi/data/redisStockData")
finance_api_port = int(os.getenv('finance_api_port', 8007))
scheduler = BackgroundScheduler(jobstores={
    'mongo': MongoDBJobStore(client=mongo_client)
})
scheduler.start()
neo4j_api_client = Neo4jApiClient("http://localhost:8003")
metamodel_utils = MetamodelUtils(redis_output_client, neo4j_api_client)
docker_client = docker.from_env()
datasource_utils = DatasourceUtils(docker_client, stock_backups_path)

app = FastAPI(title="MAGI MaC API")


def time_series_job_updated(magi_finance_port, input_redis_port, output_redis_port, is_historical):
    x = datetime.now()
    tz = pytz.timezone('America/Los_Angeles')

    x = tz.localize(x)
    hour = x.hour
    minute = x.minute
    weekday = x.weekday()

    print(f"Magi finance port:{magi_finance_port}")
    print(f"Weekday:{weekday}, hour:{hour}, minute:{minute}")

    if not is_historical:
        if weekday > 4 or not (hour > 5 or (hour == 5 and minute > 30)) or not (
                hour < 13 or (hour == 13 and minute < 31)):
            print("Market is not open yet. Time series analysis will not start.")
            return

    # Create volume container
    volume_container = docker_client.containers.run(image="time-series-core",
                                                    name=f"time-series-core-{str(uuid.uuid4())}",
                                                    detach=True,
                                                    network_mode="host",
                                                    volumes=[
                                                        "/etc/timezone:/etc/timezone:ro",
                                                        "/etc/localtime:/etc/localtime:ro"],
                                                    stdin_open=True,
                                                    tty=True,
                                                    environment={
                                                        "redis_host": "localhost",
                                                        # "redis_port": 6381,
                                                        "redis_port": input_redis_port,
                                                        "output_redis_host": "localhost",
                                                        # "output_redis_port": 6379,
                                                        "output_redis_port": output_redis_port,
                                                        "from_time": 0,
                                                        "to_time": -1,
                                                        "aggregation_type": "last",
                                                        "bucket_size_msec": 60000,
                                                        "num_regimes": 20,
                                                        "input_filters": "SYMSET=ACTIVE_" + "VOLUME",
                                                        "ts_freq_threshold": 20,
                                                        "peek_ratio": 0.3,
                                                        "enablePlotting": True,
                                                        "enablePrediction": True,
                                                        "enablePercentChange": True,
                                                        "window": 10,
                                                        "timeZone": "US/Pacific",
                                                        "output_stream_name": "MAGI_" + "VOLUME",
                                                        "process_period": 600,
                                                        "enableBatch": False,
                                                        # "enableBatch": True,
                                                        "miniBatchTimeWindow": 2,
                                                        "miniBatchSize": 5,
                                                        "enableStreaming": False,
                                                        "operation_mode": "pct",
                                                        "percent_change_event_ratio": 0.05,
                                                        "percent_change_indicator_ratio": 0.025,
                                                        "custom_changepoint_function_name": "",
                                                        "custom_changepoint_function_script": "",
                                                        "chow_penalty": 10,
                                                        "model": "l1",
                                                        "enableFillMissingDataWithLast": False,
                                                        "file_url": "",
                                                        "enableOnlineMonitor": False,
                                                        "ts_list": "test1,test2",
                                                        "subsequenceLength": 10,
                                                        "windowSize": 10,
                                                        "excl_factor": 1,
                                                        "n_regimes": 2,
                                                        "stream_refresh_rate": 10,
                                                        "percent_change_threshold": 0.05,
                                                        "percent_window": 2,
                                                        "last_minutes_count": 5,
                                                        "refresh_interval": "1s",
                                                        "dashboard_title": "My Streaming Dashboard"
                                                    })

    # Create price container
    price_container = docker_client.containers.run(image="time-series-core",
                                                   name=f"time-series-core-{str(uuid.uuid4())}",
                                                   detach=True,
                                                   network_mode="host",
                                                   volumes=[
                                                       "/etc/timezone:/etc/timezone:ro",
                                                       "/etc/localtime:/etc/localtime:ro"],
                                                   stdin_open=True,
                                                   tty=True,
                                                   environment={
                                                       "redis_host": "localhost",
                                                       # "redis_port": 6381,
                                                       "redis_port": input_redis_port,
                                                       "output_redis_host": "localhost",
                                                       # "output_redis_port": 6379,
                                                       "output_redis_port": output_redis_port,
                                                       "from_time": 0,
                                                       "to_time": -1,
                                                       "aggregation_type": "last",
                                                       "bucket_size_msec": 60000,
                                                       "num_regimes": 20,
                                                       "input_filters": "SYMSET=ACTIVE_" + "PRICE",
                                                       "ts_freq_threshold": 20,
                                                       "peek_ratio": 0.3,
                                                       "enablePlotting": True,
                                                       "enablePrediction": True,
                                                       "enablePercentChange": True,
                                                       "window": 10,
                                                       "timeZone": "US/Pacific",
                                                       "output_stream_name": "MAGI_" + "PRICE",
                                                       "process_period": 600,
                                                       "enableBatch": False,
                                                       # "enableBatch": True,
                                                       "miniBatchTimeWindow": 2,
                                                       "miniBatchSize": 5,
                                                       "enableStreaming": False,
                                                       "operation_mode": "pct",
                                                       "percent_change_event_ratio": 0.05,
                                                       "percent_change_indicator_ratio": 0.025,
                                                       "custom_changepoint_function_name": "",
                                                       "custom_changepoint_function_script": "",
                                                       "chow_penalty": 10,
                                                       "model": "l1",
                                                       "enableFillMissingDataWithLast": False,
                                                       "file_url": "",
                                                       "enableOnlineMonitor": False,
                                                       "ts_list": "test1,test2",
                                                       "subsequenceLength": 10,
                                                       "windowSize": 10,
                                                       "excl_factor": 1,
                                                       "n_regimes": 2,
                                                       "stream_refresh_rate": 10,
                                                       "percent_change_threshold": 0.05,
                                                       "percent_window": 2,
                                                       "last_minutes_count": 5,
                                                       "refresh_interval": "1s",
                                                       "dashboard_title": "My Streaming Dashboard"
                                                   })

    print("time series containers created and started to run")

    while True:
        try:
            if docker_client.containers.get(container_id=volume_container.id).status != "exited":
                time.sleep(5)
            else:
                break
        except NotFound:
            break

    print("VOLUME process ended")

    while True:
        try:
            if docker_client.containers.get(container_id=price_container.id).status != "exited":
                time.sleep(5)
            else:
                break
        except NotFound:
            break
    print("PRICE process ended")
    # remove ended containers
    prune_containers(docker_client)

    # requests.post(f'http://localhost:{finance_port}/financial_timeseries_to_neo4j',
    #               json={
    #                   "data_type": "VOLUME"
    #               }).json()
    # requests.post(f'http://localhost:{finance_port}/financial_timeseries_to_neo4j',
    #               json={
    #                   "data_type": "PRICE"
    #               }).json()
    #
    # print("financial_timeseries_to_neo4j finish")

    requests.post(f'http://localhost:{finance_api_port}/send_news_to_frontEnd',
                  json={
                      "magifinance_port": magi_finance_port,
                      "input_redis_port": output_redis_port,
                      "is_historical": is_historical
                  }).json()

    print("send_news_to_frontEnd finish")


def news_job_updated(output_redis_port: int):
    # Create news job container
    prune_containers(docker_client)
    news_job_container = docker_client.containers.run(image="magi-news-job",
                                                      name=f"magi-news-job-{str(uuid.uuid4())}",
                                                      detach=True,
                                                      network_mode="host",
                                                      stdin_open=True,
                                                      volumes=[
                                                          "/etc/timezone:/etc/timezone:ro",
                                                          "/etc/localtime:/etc/localtime:ro"],
                                                      tty=True,
                                                      environment={
                                                          "output_redis_port": output_redis_port
                                                      })
    print("News job container created")


@app.post("/start_time_series_analysis/")
def start_time_series_analysis_container(request: StartContainerRequest):
    container = docker_client.containers.run(image="time-series-core",
                                             name=f"time-series-core-{str(uuid.uuid4())}",
                                             detach=True,
                                             network_mode="host",
                                             stdin_open=True,
                                             auto_remove=True,
                                             tty=True,
                                             environment=request.dict())

    return get_container_dict(container)


@app.post("/construct_metamodel_from_ts_output/")
def construct_metamodel_from_ts_output(request: ConstructMetamodelFromTSOutputRequest):
    if request.output_name is None or not request.output_name:
        raise HTTPException(status_code=500, detail=f"Output_name parameter cannot be empty.")
    result = metamodel_utils.create_metamodel_with_ts_output(request.output_name)
    return {
        "result": result
    }


@app.post("/register_news_job/")
def register_news_job(request: RegisterNewsJobRequest):
    scheduler.add_job(news_job_updated, trigger='cron',
                      args=[6379],
                      hour=request.job_start_hour,
                      max_instances=1000000,
                      minute=request.job_start_minute,
                      name=f"news_job_at_{request.job_start_hour}_{request.job_start_minute}",
                      jobstore='mongo')

    return {
        "result": True
    }


@app.post("/register_time_series_job/")
def register_time_series_job(request: RegisterTimeSeriesJobRequest):
    scheduler.add_job(time_series_job_updated, 'cron',
                      args=[request.magi_finance_port, request.input_redis_port, request.output_redis_port,
                            request.is_historical],
                      max_instances=1000000,
                      minute=f"*/{request.job_interval}",
                      name=f"time_series_job_input_{request.input_redis_port}_output_{request.output_redis_port}_{request.job_interval}_min_{request.magi_finance_port}_port",
                      jobstore='mongo')
    return {
        "result": True
    }


@app.get("/get_registered_jobs/")
def get_registered_jobs():
    jobs = scheduler.get_jobs(jobstore='mongo')
    return [{
        "id": x.id,
        "name": x.name,
        "run_schedule": str(x.trigger),
        "next_run_time": x.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
    } for x in jobs]


@app.post("/delete_all_jobs/")
def delete_all_jobs():
    try:
        for job in scheduler.get_jobs(jobstore='mongo'):
            scheduler.remove_job(job.id, jobstore='mongo')
    except apscheduler.jobstores.base.JobLookupError:
        raise HTTPException(status_code=500, detail=f"Cannot delete all jobs.")
    return {
        "result": True
    }


@app.post("/delete_job/")
def delete_job(request: DeleteJobRequest):
    try:
        scheduler.remove_job(request.job_id, jobstore='mongo')
    except apscheduler.jobstores.base.JobLookupError:
        raise HTTPException(status_code=500, detail=f"Cannot find the job with id {request.job_id}")
    return {
        "result": True
    }


@app.post("/generic_metamodel_creation_with_nx/")
def generic_metamodel_creation_with_nx(request: GenerateMetaModelRequest):
    #  controlling parameter
    if request.redis_key is None or not request.redis_key:
        raise HTTPException(status_code=500, detail=f"Redis key parameter cannot be empty.")

    prm = request.redis_key

    start_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    # starting creation of redis object json
    metamodel_json = metamodel_utils.create_metamodel_json_for_neo4j_nx(prm)
    finish_metamodel_json_preparation = datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + " nodes:" + str(
        len(metamodel_json["nodes"])) + "relations: " + str(len(metamodel_json["relation_triplets"]))

    import json
    with open('data.json', 'w') as f:
        json.dump(metamodel_json, f)

    with ZipFile('metamodel.zip', 'w') as zip:
        zip.write("data.json")

    # starting insertion  redis json into neo4j database
    neo4j_api_client.create_graph_nx("metamodel.zip", "L2")
    end_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    return {
        "result": "Start: " + start_time +
                  "\n Metamodel data preparation: " + finish_metamodel_json_preparation +
                  "\n All operations finished: " + end_time
    }


@app.post("/start_live_streaming_trading_datasource/")
def start_live_streaming_trading_datasource(request: StartLiveStreamingTradingDataSourceRequest):
    request_dict = request.dict()
    container_dict = datasource_utils.start_live_streaming_trading_datasource(request_dict)
    return container_dict


@app.post("/start_historical_trading_data_source/")
def start_historical_trading_data_source(request: StartHistoricalTradingDataSourceRequest):
    container_dict = datasource_utils.start_historical_trading_data_source(request.date, request.dict())
    return container_dict


@app.post("/start_magi_web/")
def start_magi_web(request: StartMagiWebRequest):
    project_name, start_magi_web_code = magi_web_utils.start_magi_web(request.magi_web_mysql_port,
                                                                      request.magi_web_ui_port)
    if start_magi_web_code == 0:
        return {
            "project_name": project_name,
            "mysql_port": request.magi_web_mysql_port,
            "web_port": request.magi_web_ui_port
        }
    else:
        prune_containers(docker_client)
        raise HTTPException(status_code=500, detail=f"Cannot start new MagiFinance instance with the parameters.")


@app.post("/kill_magi_web/")
def kill_magi_web(request: KillMagiWebRequest):
    kill_magi_web_code = magi_web_utils.kill_magi_web(request.project_name)
    prune_containers(docker_client)
    if kill_magi_web_code == 0:
        return {
            "project_name": request.project_name
        }
    else:
        raise HTTPException(status_code=500, detail=f"Cannot kill the MagiFinance instance with the parameters.")


@app.post("/start_magifinance_system/")
def start_magifinance_system(request: StartHistoricalTradingDataSourceRequest):
    # Create magifinance ui and mysql db first
    random_mysql_port = find_free_port()
    random_ui_port = find_free_port()
    project_name, start_magi_web_code = magi_web_utils.start_magi_web(random_mysql_port, random_ui_port)

    # Check if magifinance instance is ready
    while True:
        try:
            if requests.get(f"http://localhost:{random_ui_port}/docs").status_code == 200:
                break
            else:
                time.sleep(3)
        except:
            time.sleep(3)

    # Create historical data source
    historical_datasource_dict = datasource_utils.start_historical_trading_data_source(request.date, request.dict())
    datasource_name = historical_datasource_dict["container_name"]
    datasource_input_redis_port = historical_datasource_dict["input_redis_port"]
    datasource_output_redis_port = historical_datasource_dict["output_redis_port"]

    # Start time series job to process data
    scheduler.add_job(time_series_job_updated, 'cron',
                      args=[random_ui_port, datasource_input_redis_port, datasource_output_redis_port, True],
                      minute=f"*/{request.ts_job_interval_minutes}",
                      name=f"time_series_job_input_{datasource_input_redis_port}_output_{datasource_output_redis_port}_{request.ts_job_interval_minutes}_min_{random_ui_port}_port",
                      jobstore='mongo',
                      max_instances=1000000)

    return {
        "project_name": project_name,
        "magifinance_mysql_port": random_mysql_port,
        "magifinance_ui_port": f"http://localhost:{random_ui_port}/finance-news",
        "historical_datasource_name": datasource_name,
        "datasource_input_redis_port": datasource_input_redis_port,
        "datasource_output_redis_port": datasource_output_redis_port
    }


if __name__ == "__main__":
    workers = int(os.getenv('api_workers', 1))
    api_port = int(os.getenv('api_port', 8000))

    print(f"MagiMonitoring is available on http://localhost:{api_port}")

    uvicorn.run("api:app", host="0.0.0.0", port=api_port, workers=workers, log_level="warning")
