import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from MNews_Analyzer_ForAPI import MNews_ForAPI
from neo4j_api_client import Neo4jApiClient
from redis import Redis

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
neo4j_api_client = Neo4jApiClient("http://localhost:8003")
mnews_api_client = MNews_ForAPI(redis_output_client, neo4j_api_client)


class CallNewsAPIRequest(BaseModel):
    symbol:str
    pageSize: int
    toNewsPublishedDate:str
    fromNewsPublishedDate:str
    industryList:list
    category:str

class NewsAPIRedisRequest(BaseModel):
    count: int
    date:str


app = FastAPI(title="News API")

@app.post("/callNewsAPI/")
async def callNewsAPI(request: CallNewsAPIRequest):
    try:
        print("start")

        result = mnews_api_client.analyzeNewsWithAPI( request.symbol, request.toNewsPublishedDate,request.fromNewsPublishedDate,request.pageSize,request.category,request.industryList )

    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return     {"result":True}

@app.post("/createNeo4jAndRedisForNews/")
async def createNeo4jAndRedisForNews(request: CallNewsAPIRequest):
    try:
        print("start")

        result = mnews_api_client.createNeo4jJsonAndRedis(request.symbol, request.toNewsPublishedDate,request.fromNewsPublishedDate,request.pageSize,request.category,request.industryList )

    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return     {"result":True}

@app.post("/getNewsFromRedis/")
async def getNewsFromRedis(request: NewsAPIRedisRequest):
    try:
        print("start")

        result = mnews_api_client.getNewsFromRedis( request.count,request.date)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return     {"result":result}

if __name__ == "__main__":
    api_port = int(os.getenv('api_port', 8202))
    uvicorn.run("NewsAPITest:app", host="0.0.0.0", port=api_port)

