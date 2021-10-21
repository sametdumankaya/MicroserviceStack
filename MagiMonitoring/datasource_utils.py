import glob
import time
import uuid

from misc import *
from docker.errors import APIError
from fastapi import HTTPException
from redis import Redis


class DatasourceUtils:
    def __init__(self, docker_client, stock_backups_path):
        self.docker_client = docker_client
        self.stock_backups_path = stock_backups_path

    def start_live_streaming_trading_datasource(self, request_dict: dict):
        request_dict["stream_type"] = "live"
        container = self.docker_client.containers.run(image="trading-data-source",
                                                      name=f"trading-data-source-{str(uuid.uuid4())}",
                                                      detach=True,
                                                      network_mode="host",
                                                      stdin_open=True,
                                                      tty=True,
                                                      environment=request_dict)
        container_dict = get_container_dict(container)
        return container_dict

    def start_historical_trading_data_source(self, date: str, request_dict: dict):
        datasource_guid = str(uuid.uuid4())
        try:
            backup_file_names = glob.glob(f"{self.stock_backups_path}/dump_{date.replace('-', '')}*")
            if len(backup_file_names) == 0:
                raise HTTPException(status_code=500, detail=f"Data for the date {date} is not available !")
            input_redis_port = find_free_port()
            output_redis_port = find_free_port()
            input_redis_container = self.docker_client.containers.run(image="redislabs/redistimeseries",
                                                                      name=f"data-source-input-{datasource_guid}",
                                                                      detach=True,
                                                                      stdin_open=True,
                                                                      tty=True,
                                                                      volumes=[
                                                                          f"{backup_file_names[0]}:/data/dump.rdb"],
                                                                      ports={f'6379/tcp': input_redis_port})
        except APIError:
            raise HTTPException(status_code=500, detail=f"Port {input_redis_port} is already in use!")

        # Wait input Redis to be available
        while True:
            try:
                Redis("localhost", input_redis_port).ping()
                break
            except:
                time.sleep(3)

        try:
            self.docker_client.containers.run(image="redislabs/redistimeseries",
                                              name=f"data-source-output-{datasource_guid}",
                                              detach=True,
                                              stdin_open=True,
                                              tty=True,
                                              ports={f'6379/tcp': output_redis_port})
        except APIError:
            self.docker_client.containers.get(input_redis_container.id).remove(force=True)
            raise HTTPException(status_code=500, detail=f"Port {output_redis_port} is already in use!")

        # Wait output Redis to be available
        while True:
            try:
                Redis("localhost", output_redis_port).ping()
                break
            except:
                time.sleep(3)

        prune_containers(self.docker_client)
        request_dict["stream_type"] = "historical"
        environment_dict = request_dict
        environment_dict["input_redis_port"] = input_redis_port
        environment_dict["output_redis_port"] = output_redis_port
        environment_dict["wait_time_msec"] = 0
        container = self.docker_client.containers.run(image="trading-data-source",
                                                      name=f"trading-data-source-{datasource_guid}",
                                                      detach=True,
                                                      network_mode="host",
                                                      stdin_open=True,
                                                      tty=True,
                                                      environment=request_dict)
        container_dict = get_container_dict(container)
        container_dict["input_redis_port"] = input_redis_port
        container_dict["output_redis_port"] = output_redis_port
        return container_dict
