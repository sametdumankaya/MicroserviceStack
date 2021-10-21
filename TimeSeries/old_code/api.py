from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import uvicorn
from timeSeriesMain import TimeSeriesOperations
import os
from io import BytesIO
import pandas as pd
import uuid


class AnalyzeTimeSeriesFileRequest(BaseModel):
    file_url: str


class InsertDataToRedisRequest(BaseModel):
    csv_file_name: str
    labels: dict


class ProcessTimeSeriesRequest(BaseModel):
    from_time: int
    to_time: int
    aggregation_type: str
    bucket_size_msec: int
    num_regimes: int
    filters: str
    ts_freq_threshold: int
    peek_ratio: float
    enablePlotting: bool
    enablePrediction: bool
    enablePercentChange: bool
    window: int
    timeZone: str
    output_name: str
    process_period: int
    enableBatch:bool
    miniBatchTimeWindow:int
    miniBatchSize:int
    enableStreaming:bool
    operation_mode:str
    model:str
    percent_change_event_ratio:float
    percent_change_indicator_ratio:float
    custom_changepoint_function_name:str
    custom_changepoint_function_script:str
    
app = FastAPI()
time_series_operations = TimeSeriesOperations(os.getenv('redis_host', "localhost"),
                                              int(os.getenv('redis_port', 6379)),
                                              os.getenv('output_redis_host', "localhost"),
                                              int(os.getenv('output_redis_port', 6379)))


@app.post("/analyze_time_series_file/")
async def analyze_time_series_file(request: AnalyzeTimeSeriesFileRequest):
    process_id = "SENSORDOG_" + str(uuid.uuid4())
    df = pd.read_csv(request.file_url)
    time_series_operations.analyze_time_series_csv(df, {
        "TARGET": process_id
    })
    return {"process_id": process_id}


@app.post("/analyze_time_series_csv/")
async def analyze_time_series_csv(csv_file: UploadFile = File(...)):
    process_id = "SENSORDOG_" + str(uuid.uuid4())
    contents = await csv_file.read()
    df = pd.read_csv(BytesIO(contents))
    time_series_operations.analyze_time_series_csv(df, {
        "TARGET": process_id
    })
    return {"process_id": process_id}


@app.post("/process_time_series/")
async def process_time_series(request: ProcessTimeSeriesRequest):
    result = time_series_operations.process_time_series(request.from_time,
                                                        request.to_time,
                                                        request.aggregation_type,
                                                        request.bucket_size_msec,
                                                        request.num_regimes,
                                                        request.filters,
                                                        request.ts_freq_threshold,
                                                        request.peek_ratio,
                                                        request.enablePlotting,
                                                        request.enablePrediction,
                                                        request.enablePercentChange,
                                                        request.window,
                                                        request.timeZone,
                                                        request.output_name,
                                                        request.process_period,
                                                        request.enableBatch,
                                                        request.miniBatchTimeWindow,
                                                        request.miniBatchSize,
                                                        request.enableStreaming,
                                                        request.operation_mode,
                                                        request.model,
                                                        request.percent_change_event_ratio,
                                                        request.percent_change_indicator_ratio,
                                                        request.custom_changepoint_function_name,
                                                        request.custom_changepoint_function_script)

    return {
        "result": result
    }


if __name__ == "__main__":
    workers = int(os.getenv('api_workers', 4))
    api_port = int(os.getenv('api_port', 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=api_port, workers=workers)
