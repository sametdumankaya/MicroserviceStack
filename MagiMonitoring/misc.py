from contextlib import closing
from docker.errors import APIError

import socket


def prune_containers(docker_client):
    try:
        docker_client.containers.prune()
    except APIError:
        pass


def get_container_dict(container):
    return {
        "container_name": container.name,
        "image_name": container.image.tags[0],
        "container_id": container.short_id,
        "startedAt": container.attrs['Created'],
        "finishedAt": None if container.status == 'running' else container.attrs['State']['FinishedAt'],
        "status": container.status,
        "logs": container.logs(tail=50).splitlines()
    }


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]