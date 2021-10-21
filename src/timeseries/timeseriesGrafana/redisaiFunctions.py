import numpy as np
import redisai
import redistimeseries
from typing import Optional
def sendModeltoRedisAI(redisai_con, model_name:str,model_type:str,model_fname:str,test_script_name=None,device=None):
    import io
    import ml2rt
    import os
    if(device is None):device="cpu"
    out1=""
    directory = os.getcwd()+'\models\\'
    model_fname=directory+model_fname
    pt_model = ml2rt.load_model(model_fname)
    con = redisai_con
    if(model_type=='torch'):
        out1 = con.modelset(model_type, model_type, device, pt_model)
    elif(model_type=='tf'):
        out1 = con.modelset(model_name, model_type, device,inputs=['input'], outputs=['output'],data=pt_model)
    elif(model_type=='onnx'):
        out1 = con.modelset(model_name, 'onnx', device, pt_model)
    if(test_script_name is not None):
        test_script_name=os.getcwd()+'\models\\'+test_script_name
        script = ml2rt.load_script(test_script_name)
        out2 = con.scriptset(test_script_name, device, script)
        
    if(out1=="OK"):
        return True
    else: 
        return False

def sendToPrediction(test_data_name:str,test_data:list,last_time_stamp:int,sampling_rate:int,model_name:str,model_type:str,output_name:str,send_to_redists:bool,redisai_con,redists_con,test_script_name=None,window_size=100,num_predictions=1000):
    con_ts=redists_con
    test_data=con_ts.range(test_data_name, 0,-1,)
    _, test_data = zip(*test_data)
    test_data=list(test_data)
    forecast_start_index=len(test_data)-window_size-num_predictions-1
    if(forecast_start_index<0):
        forecast_start_index=0
    results=[]
    last_value=test_data[-1]
    for i in range(num_predictions+1):
        test_data_chunk=test_data[forecast_start_index:window_size+forecast_start_index]
        forecast_start_index+=1
        if(forecast_start_index+window_size>=len(test_data)):break
        r=predictTsfromRedisAI(test_data_name,test_data_chunk,model_name,output_name,redisai_con,test_script_name)
        results.extend(r)
    if(not send_to_redists):
        return results
    else:
        results=[x+last_value-results[0] for x in results]
        results = [(last_time_stamp+((i)*sampling_rate), results[i]) for i in range(0, len(results))]
        try:
            con_ts.create(output_name, labels={'source':'redisai','forecast':model_name})
        except Exception as e:
            con_ts.delete(output_name)
            con_ts.create(output_name, labels={'source':'redisai','forecast':model_name})
        results=[(output_name,)+xs for xs in results]
        _=con_ts.madd(results)
    return results

def predictTsfromRedisAI(test_data_name:str,test_data_chunk:list,model_name:str,output_name:str,redisai_con,test_script_name=None):
    import numpy as np
    con_ai = redisai_con
    outp=None
    if(type(test_data_chunk)==list): 
        test_data_chunk=np.array([test_data_chunk], dtype="float32")
    try:
        _ = con_ai.tensorset(test_data_name, test_data_chunk)
        _ = con_ai.modelrun(model_name, test_data_name, output_name)
        outp=con_ai.tensorget(output_name)[0].tolist()
    except Exception as e:
        print(e)
        print("Check your redisAI connections")
    return outp