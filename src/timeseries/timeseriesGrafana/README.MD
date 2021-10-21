This folder contains dashboard and panel creation in Grafana from redistimeseries.

- Required libs & downloads:
  1. pip install -U grafana_api
  2. pip install redistimeseries
  3. Download https://github.com/RedisTimeSeries/grafana-redistimeseries
  4. Install SimpleJson plugin for grafana (grafana-cli plugins install grafana-simple-json-datasource)
  5. pip install onnx
  6. pip install keras2onnx
  7. pip install redisai
  
- Make sure Grafana is up and running

- Add SimpleJson to Grafana Data Source with host-address settings (e.g, http://localhost:4000)

- Make sure you compile the run_cython.pyx by running python setup.py (refer to the readme about cythonized structural break analysis) if you are going to add annotations to structural breaks and send them to grafana. (TODO: the Chow test and break quality control functions will be cythonized later. Make sure you re-compile run-cython once these two functions are ready in future)

- Set redis and SimpleJson server's host-names and port numbers inside the GrafanaDatastoreServer.py file before running it.

- Make sure GrafanaDatastoreServer.py under /grafana-redistimeseries is running (infinite loop for interfacing between redis and grafana).

- redisTsStreamData.py streams data to redistimeseries in an infinite loop. Run this code to stream the Wadjet dataset to redistimeseries.

- If you want to use the batch mode, redisTsStreamData.py has a function 'loadTsData' that can load the same dataset once to the redistimeseries.

- the __main__ under dfre2grafana has the example use

Notes: 
- Prefer auth=(username,password) authentication if you plan to change Grafana settings by using the grafana_api. 
- Grafana annotations are saved in database and these insertions are slow. Give some time between multiple annotations. To frequent api requests can cause some annotations to be lost.
