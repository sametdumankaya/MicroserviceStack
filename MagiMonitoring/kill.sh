#!/bin/bash

# kill the cluster and remove unnecessary containers, images, volumes
docker-compose down && docker system prune -f