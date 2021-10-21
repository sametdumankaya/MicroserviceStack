from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from typing import List
from pydantic import BaseModel
import uvicorn
import os
from metamodel_utils import MetamodelUtils
from fastapi.responses import FileResponse


class RunPipeline(BaseModel):
    pipelines: List[str] = ['tokenize', 'cleanxml', 'docdate', 'ssplit', 'pos', 'lemma', 'ner', 'entitymentions',
                            'regexner', "tokensregex", "parse", "depparse", "coref", "dcoref", "relation", "natlog",
                            "openie", "entitylink", "kbp", "quote", "quote.attribution", "sentiment", "truecase",
                            "udfeats"]
    text: str


class ConvertQuestionToGraphRequest(BaseModel):
    question: str


class CreateGraphForLongTextRequest(BaseModel):
    long_text: str


class CreateNLPGraphRequest(BaseModel):
    text: str


class SearchInGraphRequest(BaseModel):
    text: str


neo4j_api_port = int(os.getenv("neo4j_api_port", 8003))
stanford_nlp_port = int(os.getenv("stanford_nlp_port", 9000))
metamodel_utils = MetamodelUtils(neo4j_api_port, stanford_nlp_port)
app = FastAPI(title="NLU API")


@app.post("/run_pipeline_with_string/")
def run_pipeline_with_string(request: RunPipeline):
    result = metamodel_utils.process_text_with_pipelines(request.text, request.pipelines)
    return result


@app.post("/run_pipeline_with_file/")
async def run_pipeline_with_file(document: UploadFile = File(...), pipelines: List[str] = Form(...)):
    text = (await document.read()).decode("utf-8")
    result = metamodel_utils.process_text_with_pipelines(text, pipelines[0].split(","))
    return result


@app.post("/convert_question_to_graph/")
def convert_question_to_graph(request: ConvertQuestionToGraphRequest):
    result = metamodel_utils.process_question_to_graph(request.question)
    return result


@app.post("/create_nlp_graph/")
def create_nlp_graph(request: CreateNLPGraphRequest):
    result = metamodel_utils.create_nlp_graph(request.text)
    return result


@app.post("/search_in_graph/")
def search_in_graph(request: SearchInGraphRequest):
    result = metamodel_utils.search_in_graph(request.text)
    return result


@app.post("/export_whole_db_to_graphml/")
def export_whole_db_to_graphml():
    graphml_file_path = metamodel_utils.export_db_to_graphml()
    return FileResponse(graphml_file_path, media_type='application/octet-stream', filename="graph.graphml")

@app.post("/AmbiverseEntityLinking/")
def AmbiverseEntityLinking(sentence):
    try:
        result= metamodel_utils.AmbiverseEntity(sentence)
        return result
    except ValueError as e:
            raise HTTPException(status_code=500, detail=e.args)

@app.post("/ConceptnetLinking/")
def ConceptnetLinking(term):
    try:
        result = metamodel_utils.ConceptNetEntity(term)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)

@app.post("/ConstructNewsMetamodel/")
def ConstructNewsMetamodel(news):
    try:
        result = metamodel_utils.ConstructNewsMetamodel(news)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=e.args)


if __name__ == "__main__":
    api_port = int(os.getenv('api_port', 8004))
    uvicorn.run(app, host="0.0.0.0", port=api_port, log_level="warning")
