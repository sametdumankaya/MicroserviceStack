import datetime
import json
from fastapi import FastAPI
from redis import Redis
import uvicorn
import os
from annotation_utils import AnnotationsUtils
from fastapi.middleware.cors import CORSMiddleware
import random

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

app = FastAPI(title="Annotation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

annotation_utils = AnnotationsUtils(redis_output_client)


@app.get("/get_streaming_data/")
def get_streaming_data():
    result_redis = {}
    redis_stream_data = annotation_utils.get_redis_data("poc_data_html")
    data_dict = redis_stream_data[0][1]
    for data in data_dict:
        # data = json.loads("")

        data_jsn = json.loads(data_dict[data])

        th = str(data_jsn["threshold"])
        vl = str(data_jsn["value"])
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if vl < th:
            result_redis[data] = {"color": "red",
                                  "messages": f"{now_str} - There is " + data + " problem.Threshold:" + th + "-Value:" + vl}
        else:
            result_redis[data] = {"color": "green",
                                  "messages": f"{now_str} - There is no " + data + " problem.Threshold:" + th + "-Value:" + vl}

    return {
        "result": result_redis
    }


@app.get("/get_streaming_data_floor_plan_blackhole/")
def get_streaming_data_floor_plan_blackhole():
    keys = ["Leaf5", "Leaf6", "Leaf7", "Leaf8", "sswB3",
            "rswB1", "Spine2", "Spine3", "Spine4", "Spine5", "Spine6", "dr03", "Spine1", "rswA4A", "rswA5A", "rswA6A",
            "Leaf1", "Leaf2", "Leaf3", "Leaf4", "dr02", "rswB6", "dr01"]
    result_redis = {}
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    queue_entry = {
        x: json.dumps({"value": random.randint(82, 100), "threshold": random.randint(0, 100)}) for x in keys
    }
    result_redis["message"] = f"{now_str} - Systems nominal."

    if 10 < annotation_utils.blackhole_time_counter < 30:
        queue_entry["Leaf3"] = json.dumps({"value": random.randint(0, 48), "threshold": random.randint(0, 100)})
        queue_entry["dr01"] = json.dumps({"value": random.randint(51, 80), "threshold": random.randint(0, 100)})
        result_redis["message"] = f"{now_str} - There are problems in Leaf3 and dr01."

    result_redis["B1"] = {"color": "green",
                          "messages": ""}
    result_redis["B1_alt"] = {"color": "green",
                              "messages": ""}
    result_redis["B2"] = {"color": "green",
                          "messages": ""}
    result_redis["B3"] = {"color": "green",
                          "messages": ""}
    result_redis["B4"] = {"color": "green",
                          "messages": ""}

    result_redis["B5"] = {"color": "green",
                          "messages": ""}
    result_redis["B5_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["B6"] = {"color": "green",
                          "messages": ""}
    result_redis["B6_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["A1"] = {"color": "green",
                          "messages": ""}
    result_redis["A2"] = {"color": "green",
                          "messages": ""}
    result_redis["A3"] = {"color": "green",
                          "messages": ""}

    result_redis["A4"] = {"color": "green",
                          "messages": ""}
    result_redis["A4_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["A5"] = {"color": "green",
                          "messages": ""}
    result_redis["A5_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["A6"] = {"color": "green",
                          "messages": ""}
    result_redis["A6_alt"] = {"color": "green",
                              "messages": ""}

    for data in keys:
        data_jsn = json.loads(queue_entry[data])
        th = str(data_jsn["threshold"])
        vl = data_jsn["value"]


        if vl >= 81:
            result_redis[data] = {"color": "green",
                                  "messages": f"{now_str} - There is no " + data + " problem. Value:" + str(vl)}
        elif vl > 50:
            result_redis[data] = {"color": "yellow",
                                  "messages": f"{now_str} - There is " + data + " problem. Value:" + str(vl)}
            if data == "rswB1":
                result_redis["B1"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B1_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if (
                    data == "Leaf5" or data == "Leaf6" or data == "Leaf7" or data == "Leaf8" or data == "sswB3" or data == "dr03") and \
                    result_redis["B3"]["color"] != "red":
                result_redis["B3"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B3_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if (
                    data == "Spine1" or data == "Spine2" or data == "Spine3" or data == "Spine4" or data == "Spine5" or data == "Spine6" or data == "dr02") and \
                    result_redis["B4"]["color"] != "red":
                result_redis["B4"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}

            if (data == "Leaf1" or data == "Leaf2" or data == "Leaf3" or data == "Leaf4") and result_redis["B5"][
                "color"] != "red":
                result_redis["B5"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B5_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if (data == "rswB6" or data == "dr01") and result_redis["B6"]["color"] != "red":
                result_redis["B6"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B6_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA4A":
                result_redis["A4"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A4_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA5A":
                result_redis["A5"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A5_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA6A":
                result_redis["A6"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A6_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}
        elif vl <= 50:
            result_redis[data] = {"color": "red",
                                  "messages": f"{now_str} - There is " + data + " problem. Value:" + str(vl)}
            if data == "rswB1":
                result_redis["B1"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B1_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "Leaf5" or data == "Leaf6" or data == "Leaf7" or data == "Leaf8" or data == "sswB3" or data == "dr03":
                result_redis["B3"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B3_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "Spine1" or data == "Spine2" or data == "Spine3" or data == "Spine4" or data == "Spine5" or data == "Spine6" or data == "dr02":
                result_redis["B4"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}

            if data == "Leaf1" or data == "Leaf2" or data == "Leaf3" or data == "Leaf4":
                result_redis["B5"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B5_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswB6" or data == "dr01":
                result_redis["B6"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B6_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA4A":
                result_redis["A4"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A4_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA5A":
                result_redis["A5"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A5_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA6A":
                result_redis["A6"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A6_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

    annotation_utils.blackhole_time_counter += 1
    return {
        "result": result_redis
    }


@app.get("/get_streaming_data_floor_plan_portshutdown/")
def get_streaming_data_floor_plan_portshutdown():
    keys = ["Leaf5", "Leaf6", "Leaf7", "Leaf8", "sswB3",
            "rswB1", "Spine2", "Spine3", "Spine4", "Spine5", "Spine6", "dr03", "Spine1", "rswA4A", "rswA5A", "rswA6A",
            "Leaf1", "Leaf2", "Leaf3", "Leaf4", "dr02", "rswB6", "dr01"]
    result_redis = {}
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    queue_entry = {
        x: json.dumps({"value": random.randint(82, 100), "threshold": random.randint(0, 100)}) for x in keys
    }
    result_redis["message"] = f"{now_str} - Systems nominal."

    if 10 < annotation_utils.portshutdown_time_counter < 30:
        queue_entry["dr01"] = json.dumps({"value": random.randint(0, 48), "threshold": random.randint(0, 100)})
        queue_entry["dr03"] = json.dumps({"value": random.randint(51, 80), "threshold": random.randint(0, 100)})
        result_redis["message"] = f"{now_str} - There are problems in dr01 and dr03."

    result_redis["B1"] = {"color": "green",
                          "messages": ""}
    result_redis["B1_alt"] = {"color": "green",
                              "messages": ""}
    result_redis["B2"] = {"color": "green",
                          "messages": ""}
    result_redis["B3"] = {"color": "green",
                          "messages": ""}
    result_redis["B4"] = {"color": "green",
                          "messages": ""}

    result_redis["B5"] = {"color": "green",
                          "messages": ""}
    result_redis["B5_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["B6"] = {"color": "green",
                          "messages": ""}
    result_redis["B6_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["A1"] = {"color": "green",
                          "messages": ""}
    result_redis["A2"] = {"color": "green",
                          "messages": ""}
    result_redis["A3"] = {"color": "green",
                          "messages": ""}

    result_redis["A4"] = {"color": "green",
                          "messages": ""}
    result_redis["A4_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["A5"] = {"color": "green",
                          "messages": ""}
    result_redis["A5_alt"] = {"color": "green",
                              "messages": ""}

    result_redis["A6"] = {"color": "green",
                          "messages": ""}
    result_redis["A6_alt"] = {"color": "green",
                              "messages": ""}

    for data in keys:
        data_jsn = json.loads(queue_entry[data])
        th = str(data_jsn["threshold"])
        vl = data_jsn["value"]


        if vl >= 81:
            result_redis[data] = {"color": "green",
                                  "messages": f"{now_str} - There is no " + data + " problem. Value:" + str(vl)}
        elif vl > 50:
            result_redis[data] = {"color": "yellow",
                                  "messages": f"{now_str} - There is " + data + " problem. Value:" + str(vl)}
            if data == "rswB1":
                result_redis["B1"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B1_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if (
                    data == "Leaf5" or data == "Leaf6" or data == "Leaf7" or data == "Leaf8" or data == "sswB3" or data == "dr03") and \
                    result_redis["B3"]["color"] != "red":
                result_redis["B3"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B3_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if (
                    data == "Spine1" or data == "Spine2" or data == "Spine3" or data == "Spine4" or data == "Spine5" or data == "Spine6" or data == "dr02") and \
                    result_redis["B4"]["color"] != "red":
                result_redis["B4"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}

            if (data == "Leaf1" or data == "Leaf2" or data == "Leaf3" or data == "Leaf4") and result_redis["B5"][
                "color"] != "red":
                result_redis["B5"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B5_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if (data == "rswB6" or data == "dr01") and result_redis["B6"]["color"] != "red":
                result_redis["B6"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B6_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA4A":
                result_redis["A4"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A4_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA5A":
                result_redis["A5"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A5_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA6A":
                result_redis["A6"] = {"color": "yellow",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A6_alt"] = {"color": "yellow",
                                          "messages": f"{now_str} - There is " + data + " problem."}
        elif vl <= 50:
            result_redis[data] = {"color": "red",
                                  "messages": f"{now_str} - There is " + data + " problem. Value:" + str(vl)}
            if data == "rswB1":
                result_redis["B1"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B1_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "Leaf5" or data == "Leaf6" or data == "Leaf7" or data == "Leaf8" or data == "sswB3" or data == "dr03":
                result_redis["B3"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B3_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "Spine1" or data == "Spine2" or data == "Spine3" or data == "Spine4" or data == "Spine5" or data == "Spine6" or data == "dr02":
                result_redis["B4"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}

            if data == "Leaf1" or data == "Leaf2" or data == "Leaf3" or data == "Leaf4":
                result_redis["B5"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B5_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswB6" or data == "dr01":
                result_redis["B6"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["B6_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA4A":
                result_redis["A4"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A4_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA5A":
                result_redis["A5"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A5_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

            if data == "rswA6A":
                result_redis["A6"] = {"color": "red",
                                      "messages": f"{now_str} - There is " + data + " problem."}
                result_redis["A6_alt"] = {"color": "red",
                                          "messages": f"{now_str} - There is " + data + " problem."}

    annotation_utils.portshutdown_time_counter += 1
    return {
        "result": result_redis
    }


if __name__ == "__main__":
    workers = int(os.getenv('api_workers', 1))
    api_port = int(os.getenv('api_port', 8009))
    print(f"AnnotationAPI is available on http://localhost:{api_port}")
    uvicorn.run(app, host="0.0.0.0", port=api_port, workers=workers, log_level="warning")
