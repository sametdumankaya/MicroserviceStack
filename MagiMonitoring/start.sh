#!/bin/bash

cd ..
cd TimeSeries
docker build -t time-series-core .

# build algotrading datasource image
cd ..
cd AlgoTrading
docker build -t trading-data-source .

# build magi-news-job image
cd ..
cd NewsJob
docker build -t magi-news-job .

cd ..
cd MagiMonitoring

# run the cluster
docker-compose up --build