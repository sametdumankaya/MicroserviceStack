import os
from datetime import datetime
from zipfile import ZipFile

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from redis import Redis
import nltk

from apiCall import *
from finance_utils import FinanceUtils
from graphml_utils import GraphmlUtils
from msig_api_client import MSigClient
from neo4j_client import Neo4jClient
from news_utils import NewsUtils
from typing import Optional


class InsertNeo4jFinancalTimesSeriesRequest(BaseModel):
    data_type: str
    # there are two different data type
    # 1. 'VOLUME' which used for volume events
    # 2. 'PRICE' which used for price events


class CreateFinanceTimeSeriesRequest(BaseModel):
    data_type: str


class SendNewsToFrontendRequest(BaseModel):
    magifinance_port: int
    curated_news_topics: Optional[str]
    input_redis_port: Optional[int]
    is_historical: bool


class GetNewsBetweenDatesRequest(BaseModel):
    startDate: str
    endDate: str


class CallNewsAPIRequest(BaseModel):
    symbol: str
    pageSize: int
    toNewsPublishedDate: str
    fromNewsPublishedDate: str
    industryList: list
    category: str


class NewsAPIRedisRequest(BaseModel):
    count: int
    date: str


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

nltk.download('stopwords')
nltk.download('vader_lexicon')
neo4j_api_client = Neo4jClient("http://localhost:8003")
msig_api_client = MSigClient("http://localhost:8202")
news_utils = NewsUtils(redis_output_client, neo4j_api_client)
finance_utils = FinanceUtils(redis_output_client, neo4j_api_client, msig_api_client, news_utils)
graphml_utils = GraphmlUtils(neo4j_api_client)

app = FastAPI(title="Financial Time Series to NEo4j API")


@app.post("/financial_timeseries_to_neo4j/")
def financial_timeseries_to_neo4j(request: InsertNeo4jFinancalTimesSeriesRequest):
    #  controlling parameter
    if request.data_type is None or not request.data_type:
        raise HTTPException(status_code=500, detail=f"Data_type parameter cannot be empty.")

    prm = "MAGI_{0}".format(request.data_type)

    start_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    # starting creation of raw graphml json
    graphml_json = graphml_utils.create_neo4j_graphl_with_file("finL2Extension.graphml")

    finish_graph_preparation = " " + datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    import json
    with open('graphml_json.json', 'w') as f:
        json.dump(graphml_json, f)

    with ZipFile('graphml.zip', 'w') as zip:
        zip.write("graphml_json.json")

    # starting insertion  raw graphml json into neo4j database
    rslt_nx_graphml = neo4j_api_client.create_graph_nx("graphml.zip", "L2")

    # result_graphml = neo4j_api_client.create_graph(graphml_json)
    finish_import_graphml = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    # test dummy data
    # f = open("data.json", "r")
    # x = f.read()
    # redis_json = json.loads(x)

    # starting creation of redis object json
    redis_json = finance_utils.create_json_via_redis(prm)
    finish_redis_data_preparation = datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + " nodes:" + str(
        len(graphml_json["nodes"])) + "relations: " + str(len(graphml_json["relation_triplets"]))

    import json
    with open('data.json', 'w') as f:
        json.dump(redis_json, f)

    finish_redis_dumps = datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + " nodes:" + str(
        len(redis_json["nodes"])) + " relations: " + str(len(redis_json["relation_triplets"]))

    with ZipFile('redis.zip', 'w') as zip:
        zip.write("data.json")

    # starting insertion  redis json into neo4j database
    rslt_nx_graphml = neo4j_api_client.create_graph_nx("redis.zip", "L2")
    endTime = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    return {
        "result": "Start: " + start_time +
                  "\n Graphml data preparation: " + finish_graph_preparation +
                  "\n Graphml neo4j insertion: " + finish_import_graphml +
                  "\n Redis data preparation: " + finish_redis_data_preparation +
                  "\n Redis json dumps: " + finish_redis_dumps +
                  "\n All operations finished: " + endTime
    }


@app.post("/create_finance_time_series/")
def create_finance_time_series(request: CreateFinanceTimeSeriesRequest):
    return ApiCall.Call(request.data_type)


@app.post("/send_news_to_frontEnd/")
def send_news_to_frontEnd(request: SendNewsToFrontendRequest):
    if request.input_redis_port is not None or request.input_redis_port != 0:
        current_redis_output_client = Redis(host="localhost",
                                            port=request.input_redis_port,
                                            decode_responses=True)
        volume_data = current_redis_output_client.xrevrange("MAGI_VOLUME", count=1)
        price_data = current_redis_output_client.xrevrange("MAGI_PRICE", count=1)
    else:
        volume_data = redis_output_client.xrevrange("MAGI_VOLUME", count=1)
        price_data = redis_output_client.xrevrange("MAGI_PRICE", count=1)
    volume_data_dict = json.loads(volume_data[0][1]["data"])
    price_data_dict = json.loads(price_data[0][1]["data"])
    print("send_news")

    df_price_data_json = json.loads(price_data_dict["df_data"])
    df_data_p = {k.split(':')[3]: v for k, v in df_price_data_json.items()}
    df_price_data = pd.DataFrame(df_data_p)
    ts_price = price_data_dict["metadata"]["ts_all"]
    ts_price_min = price_data_dict["metadata"]["min_ts"]
    ts_price_max = price_data_dict["metadata"]["max_ts"]
    indicators_price = pd.DataFrame(price_data_dict["indicators"])
    events_price = pd.DataFrame(price_data_dict["events"])

    df_volume_data_json = json.loads(volume_data_dict["df_data"])
    df_data_v = {k.split(':')[3]: v for k, v in df_volume_data_json.items()}
    df_volume_data = pd.DataFrame(df_data_v)
    ts_volume = volume_data_dict["metadata"]["ts_all"]
    ts_volume_min = volume_data_dict["metadata"]["min_ts"]
    ts_volume_max = volume_data_dict["metadata"]["max_ts"]
    indicators_volume = pd.DataFrame(volume_data_dict["indicators"])
    events_volume = pd.DataFrame(volume_data_dict["events"])

    all_data = {}

    all_data["df_price_data"] = df_price_data
    all_data["ts_price"] = ts_price
    all_data["ts_price_min"] = ts_price_min
    all_data["ts_price_max"] = ts_price_max

    all_data["df_volume_data"] = df_volume_data
    all_data["ts_volume"] = ts_volume
    all_data["ts_volume_min"] = ts_volume_min
    all_data["ts_volume_max"] = ts_volume_max

    all_ts_price = list(range(price_data_dict["metadata"]["min_ts"], price_data_dict["metadata"]["max_ts"] + 60000,
                              60000))

    all_ts_volume = list(range(volume_data_dict["metadata"]["min_ts"], volume_data_dict["metadata"]["max_ts"] + 60000,
                               60000))

    start = time.time()
    df_market_capital_price = finance_utils.getMarketCapitalPerEvent_v2(all_data, events_price, indicators_price)
    print(time.time() - start, "sec. to df_market_capital_price")
    # start = time.time()
    # df_market_capital_price = finance_utils.getMarketCapitalPerEvent(all_ts_price, price_data_dict,
    #                                                                  price_data_dict["events"],
    #                                                                  price_data_dict["indicators"],
    #                                                                  price_data_dict["df_data"],
    #                                                                  volume_data_dict["df_data"],
    #                                                                  )
    # print(time.time() - start, "sec. to df_market_capital_price")

    start = time.time()
    df_market_capital_volume = finance_utils.getMarketCapitalPerEvent_v2(all_data, events_volume, indicators_volume)
    print(time.time() - start, "sec. to df_market_capital_volume")
    # start = time.time()
    # df_market_capital_volume = finance_utils.getMarketCapitalPerEvent(all_ts_volume, volume_data_dict,
    #                                                                   volume_data_dict["events"],
    #                                                                   volume_data_dict["indicators"],
    #                                                                   price_data_dict["df_data"],
    #                                                                   volume_data_dict["df_data"],
    #                                                                   )
    # print(time.time() - start, "sec. to df_market_capital_volume")

    start = time.time()
    df_sectors_price, df_industries_price = finance_utils.getSectorIndustryPerEvent_v2(indicators_price,
                                                                                       "finL2Extension.graphml")
    print(time.time() - start, "sec. to df_sectors_price")
    # start = time.time()
    # df_sectors_price, df_industries_price = finance_utils.getSectorIndustryPerEvent(price_data_dict["indicators"],
    #                                                                                 "finL2Extension.graphml")
    #
    # print(time.time() - start, "sec. to df_sectors_price")
    start = time.time()
    df_sectors_volume, df_industries_volume = finance_utils.getSectorIndustryPerEvent_v2(indicators_volume,
                                                                                         "finL2Extension.graphml")
    print(time.time() - start, "sec. to df_sectors_volume")
    # start = time.time()
    # df_sectors_volume, df_industries_volume = finance_utils.getSectorIndustryPerEvent(volume_data_dict["indicators"],
    #                                                                                   "finL2Extension.graphml")
    #
    # print(time.time() - start, "sec. to df_sectors_volume")

    start = time.time()
    msig_data = {"loop_num": volume_data_dict["metadata"]["loop_no"], "ts_price": price_data_dict["metadata"]["ts_all"],
                 "ts_volume": volume_data_dict["metadata"]["ts_all"],
                 "events_price": events_price, "events_volume": events_volume,
                 "indicators_price": indicators_price, "indicators_volume": indicators_volume,
                 "df_sectors_price": df_sectors_price, "df_industries_price": df_industries_price,
                 "df_sectors_volume": df_sectors_volume, "df_industries_volume": df_industries_volume,
                 "df_market_capital_price": df_market_capital_price,
                 "df_market_capital_volume": df_market_capital_volume,
                 "ts_price_min": price_data_dict["metadata"]["min_ts"],
                 "ts_price_max": price_data_dict["metadata"]["max_ts"],
                 "ts_volume_min": volume_data_dict["metadata"]["min_ts"],
                 "ts_volume_max": volume_data_dict["metadata"]["max_ts"]}

    finance_utils.sendNewsToFrontEnd_v2(msig_data, df_market_capital_price, df_market_capital_volume,
                                        num_events_price_gain=0, num_events_volume_gain=0,
                                        isStartofDay=True,
                                        url=f'http://localhost:{request.magifinance_port}/Events/PostEvents',
                                        curated_news_topics=request.curated_news_topics if request.curated_news_topics is not None and request.curated_news_topics != "" else 'Politics,COVID-19,Bitcoin,Supply Chain Disruption 2021',
                                        is_historical=request.is_historical, redis_port=request.input_redis_port)
    print(time.time() - start, "sec. to send_to_front_end")
    # start = time.time()
    # msig_data = {"loop_num": volume_data_dict["metadata"]["loop_no"], "ts_price": price_data_dict["metadata"]["ts_all"], "ts_volume": volume_data_dict["metadata"]["ts_all"], \
    #              "events_price": price_data_dict["events"], "events_volume": volume_data_dict["events"], \
    #              "indicators_price":price_data_dict["indicators"] , "indicators_volume": volume_data_dict["indicators"] , \
    #              "df_sectors_price": df_sectors_price, "df_industries_price": df_industries_price, \
    #              "df_sectors_volume": df_sectors_volume, "df_industries_volume": df_industries_volume, \
    #              "df_market_capital_price": df_market_capital_price,
    #              "df_market_capital_volume": df_market_capital_volume, \
    #              "ts_price_min": price_data_dict["metadata"]["min_ts"], "ts_price_max": price_data_dict["metadata"]["max_ts"],
    #              "ts_volume_min": volume_data_dict["metadata"]["min_ts"], "ts_volume_max": volume_data_dict["metadata"]["max_ts"]}
    #
    # finance_utils.sendNewsToFrontEnd(msig_data,  df_market_capital_price, df_market_capital_volume,
    #                    num_events_price_gain=0, num_events_volume_gain=0,
    #                    isStartofDay=True, url=f'http://localhost:{request.magifinance_port}/Events/PostEvents')


@app.post("/getNewsFromRedisBetweenDates/")
def getNewsFromRedisBetweenDates(request: GetNewsBetweenDatesRequest):
    try:
        print("start")

        result = news_utils.getNewsFromRedisBetweenDates(request.startDate, request.endDate)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {"result": result}


@app.post("/callNewsAPI/")
def callNewsAPI(request: CallNewsAPIRequest):
    try:
        print("start")

        result = news_utils.analyzeNewsWithAPI(request.symbol, request.toNewsPublishedDate,
                                               request.fromNewsPublishedDate, request.pageSize, request.category,
                                               request.industryList)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {"result": True}


@app.post("/createNeo4jAndRedisForNews/")
def createNeo4jAndRedisForNews(request: CallNewsAPIRequest):
    try:
        print("start")

        news_utils.createNeo4jJsonAndRedis(request.symbol, request.toNewsPublishedDate,
                                           request.fromNewsPublishedDate, request.pageSize, request.category,
                                           request.industryList)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {"result": True}


@app.post("/getNewsFromRedis/")
def getNewsFromRedis(request: NewsAPIRedisRequest):
    try:
        print("start")

        result = news_utils.getNewsFromRedis(request.count, request.date)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {"result": result}


if __name__ == "__main__":
    workers = int(os.getenv('api_workers', 1))
    api_port = int(os.getenv('api_port', 8007))
    uvicorn.run("api:app", host="0.0.0.0", port=api_port, workers=workers)
