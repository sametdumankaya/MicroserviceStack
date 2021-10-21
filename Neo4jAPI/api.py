import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from pydantic import BaseModel
from typing import Optional
from neo4j_utils import Neo4jUtils
from fastapi.logger import logger as fastapi_logger
from logging.handlers import RotatingFileHandler
import logging
import json
from datetime import datetime
import uuid
import zipfile


class CreateNodeRequest(BaseModel):
    name: str
    level: str
    properties: dict


class FindNodeIdRequest(BaseModel):
    name: str
    level: str


class AddAntisymmetricRelationRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    relation_name: str
    relation_properties: dict


class AddAntisymmetricIntensionRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    relation_properties: dict


class AddAntisymmetricExtensionRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    relation_properties: dict


class AddSymmetricRelationRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    relation_name: str
    relation_properties: dict


class FollowsTemporally(BaseModel):
    start_node_id: int
    end_node_id: int
    how_long: Optional[str] = ""
    how_many: int
    contribution_amount: Optional[float] = None


class CreateGraphRequest(BaseModel):
    graph_dict: dict
    merge_nodes_level: str


class SearchGraphForNLPRequest(BaseModel):
    text: str


utils = Neo4jUtils()
app = FastAPI(title="Neo4j API")


def put_log(api_name: str, request_params: dict, client_ip: str):
    fastapi_logger.info(
        f"{api_name}    {json.dumps(request_params)}    {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}    {client_ip}")


@app.post("/create_node/")
def create_node(request: CreateNodeRequest, base_request: Request):
    try:
        result = utils.create_node(request.name, request.level, request.properties)
        put_log(create_node.__name__, request.dict(), base_request.client.host)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {
        "node_id": result.identity
    }


@app.post("/find_node_id/")
def find_node_id(request: FindNodeIdRequest):
    try:
        result = utils.find_node_id(request.name, request.level)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {
        "node_id": result
    }


@app.post("/add_antisymmetric_relation/")
def add_antisymmetric_relation(request: AddAntisymmetricRelationRequest, base_request: Request):
    start_node = utils.get_node_by_id(request.start_node_id)
    end_node = utils.get_node_by_id(request.end_node_id)
    if start_node is None or end_node is None:
        raise HTTPException(status_code=500, detail="Cannot find start or end node with id.")
    result = utils.add_antisymmetric_relation(start_node, end_node, request.relation_name, request.relation_properties)
    put_log(add_antisymmetric_relation.__name__, request.dict(), base_request.client.host)
    return {
        "relationship_id": result.identity
    }


@app.post("/add_intension/")
def add_intension(request: AddAntisymmetricIntensionRequest, base_request: Request):
    start_node = utils.get_node_by_id(request.start_node_id)
    end_node = utils.get_node_by_id(request.end_node_id)
    if start_node is None or end_node is None:
        raise HTTPException(status_code=500, detail="Cannot find start or end node with id.")
    try:
        result = utils.add_intension(start_node, end_node, request.relation_properties)
        put_log(add_intension.__name__, request.dict(), base_request.client.host)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {
        "relationship_id": result.identity
    }


@app.post("/add_extension/")
def add_extension(request: AddAntisymmetricExtensionRequest, base_request: Request):
    start_node = utils.get_node_by_id(request.start_node_id)
    end_node = utils.get_node_by_id(request.end_node_id)
    if start_node is None or end_node is None:
        raise HTTPException(status_code=500, detail="Cannot find start or end node with id.")
    try:
        result = utils.add_extension(start_node, end_node, request.relation_properties)
        put_log(add_extension.__name__, request.dict(), base_request.client.host)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {
        "relationship_id": result.identity
    }


@app.post("/add_symmetric_relation/")
def add_symmetric_relation(request: AddSymmetricRelationRequest, base_request: Request):
    start_node = utils.get_node_by_id(request.start_node_id)
    end_node = utils.get_node_by_id(request.end_node_id)
    if start_node is None or end_node is None:
        raise HTTPException(status_code=500, detail="Cannot find start or end node with id.")
    try:
        result1, result2 = utils.add_symmetric_relation(start_node, end_node, request.relation_name,
                                                        request.relation_properties)
        put_log(add_symmetric_relation.__name__, request.dict(), base_request.client.host)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {
        "relationship_id_1": result1.identity,
        "relationship_id_2": result2.identity
    }


@app.post("/follows_temporally/")
def follows_temporally(request: FollowsTemporally, base_request: Request):
    start_node = utils.get_node_by_id(request.start_node_id)
    end_node = utils.get_node_by_id(request.end_node_id)
    if start_node is None or end_node is None:
        raise HTTPException(status_code=500, detail="Cannot find start or end node with id.")
    try:
        result = utils.follows_temporally(start_node, end_node, request.how_many,
                                          request.how_long, request.contribution_amount)
        put_log(follows_temporally.__name__, request.dict(), base_request.client.host)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args)
    return {
        "relationship_id": result.identity
    }


@app.post("/export_db_to_graphml/")
def export_db_to_graphml():
    graphml_file_path = utils.export_db_to_graphml()
    return {
        "file_path": graphml_file_path
    }


@app.post("/create_graph/")
def create_graph(request: CreateGraphRequest):
    result = utils.create_graph_nx(request.graph_dict, request.merge_nodes_level)
    return {
        "result": result
    }


@app.post("/create_graph_nx/")
async def create_graph_nx(zip_file: UploadFile = File(...), merge_nodes_level: str = "L2"):
    # if zip_file.content_type != 'application/zip':
    #     raise HTTPException(status_code=500, detail="Please provide a zip file.")
    contents = await zip_file.read()
    file_location = str(uuid.uuid4()) + ".zip"
    with open(file_location, "wb+") as file_object:
        file_object.write(contents)
    archive = zipfile.ZipFile(file_location, 'r')
    graph_dict = json.loads(archive.read(archive.filelist[0].filename).decode())
    os.remove(file_location)
    result = utils.create_graph_nx(graph_dict, merge_nodes_level)
    return {
        "result": result
    }


@app.post("/search_graph_for_nlp/")
def search_graph_for_nlp(request: SearchGraphForNLPRequest):
    result = utils.search_graph_for_nlp(request.text)
    return {
        "result": result
    }


if __name__ == "__main__":
    handler = RotatingFileHandler('magi.log', maxBytes=1000000)
    logging.getLogger().setLevel(logging.NOTSET)
    fastapi_logger.addHandler(handler),
    # temple edit
    # api_port = int(os.getenv('api_port', 8006))
    api_port = int(os.getenv('api_port', 8003))
    print(f"Neo4jAPI is available on http://localhost:{api_port}")
    uvicorn.run(app, host="0.0.0.0", port=api_port, log_level="warning")
