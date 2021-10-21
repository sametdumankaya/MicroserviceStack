# SensorDog4TimeSeries

This repository contains the core functionality for time series processing. It uses Redis Time Series (https://oss.redislabs.com/redistimeseries/), Redis Stream (https://redis.io/topics/streams-intro), Matrix Profile (https://matrixprofile.org/, https://www.cs.ucr.edu/~eamonn/MatrixProfile.html), Chow Test (https://en.wikipedia.org/wiki/Chow_test) and many other building blocks to process time series, create a descriptive model and a predictive model. The output is put to Redis as a serialized dictionary object for ingestion. 


## Parameters

- 'redis_host' : Hostname of the redis timeseries for input. Default is "localhost".
- 'redis_port' : Portname of the redis timeseries for input. Default is 6379.
- 'output_redis_host' : Hostname of the redis timeseries for output. Default is "localhost".
- 'output_redis_port' :Portname of the redis timeseries for output Default is 6379. 
- 'from_time' : End time for querying the redis timeseries input. Default is 0 which means now. 
- 'to_time' : Start time for querying the redis timeseries input. Default is -1 which means everything from the beginning.
- 'aggregation_type' : Aggregation type for querying timeseries (min, max, sum, last, etc.) Default is "last".
- 'bucket_size_msec' : Aggregation bucket size for querying timeseries. Default is 1200000. Your sampling rate must be smaller than the bucket size.
- 'num_regimes' : Max number of regimes expected from a timeseries regime change analysis. Default is 20.
- 'filters' : filter names for labeled time series in redis. Labeling the input timeseries allows faster querying. Default is "TARGET=SENSORDOG".
- 'ts_freq_threshold' : Threshold value for number of simultaneous regime changes for event detection. Default is 50 meaning that when 50 time series change their behavior simultaneously, Sensor4TimeSeries will consider it as an important point of time.
- 'peek_ratio' : Threshold value for peeks on histogram for event detection. The tallest histogram item and anything that is greater than equal to |peek_ratio| X |tallest_item| will be considered as an events. This is used by Matrix Profile algorithm and Chow Algorithms. Default is 0.3.
- 'enablePlotting' :  Enable plotting of histograms and events. Plots are converted to base64 string and added into the output for Redis stream.  Default is True.
- 'enablePrediction' : Enable prediction based on event analysis. Note that predictive model creation, training  and testing slow down the process.  Default is True.
- 'enablePercentChange' : Use deltas instead of raw timeseries data. Useful if set True for analyzing time series that are increasing counters or magnitude-wise different from other time series. Default is True. 
- 'window' : Windows size (a sliding window of samples) to perform the regime change analysis for Matrix Profile. If Percent Change is used, this window size is used as period to calculate percentages. Default is 10.
- 'timeZone' : Timezone for times tamps for display purposes. It does not affect the analyses. Default is "US/Pacific".
- 'output_name' : Name for the redis stream object to output the results. Default is OUTPUT_SENSORDOG. 
- 'process_period': The perid for batch processing loop in seconds. Default is 600.
- 'enableBatch': When enabled, the system loops through the time series processing. The system creates a temporary variable in the output Redis. You can either set this variable to True or use the MAGI MaC Api to terminate the loop.  Default is False.
- 'miniBatchTimeWindow': When streaming is enabled, the system reprocesses the last window of data in a loop if there are new data points of size miniBatchTimeWindow. Default is 2.
- 'miniBatchSize': When streaming is enabled, the system reprocesses the last miniBatchSize of data in a loop. Default is 200 hundred.
- 'enableStreaming': When enabled, the system analyzes the streaming data. The system creates a temporary variable in the output Redis. You can either set this variable to True or use the MAGI MaC Api to terminate the loop. Note that if enabled, you must have at least miniBatchSize data points aggregated data points in the input Redis time series, which is also related to bucket_size_msec parameter. Default is False.
- 'operation_mode': The system supports 4 operation modes "mp":Matrix profile, "chow":Chow Test, "pct":"Percent Change Analysis", and "custom":User-defined change-point script. Default is "mp".
- 'percent_change_event_ratio': If operation_mode is "pct", any increase higher than this value or lower than its negative are considered for event analysis. Default is 0.05 meaning that when there is a global percentage increase >= 0.05 or decrease <= -0.05, something important might have happened.
- 'percent_change_indicator_ratio': If operation_mode is "pct", any time series showing behavioral change  higher than this value or lower than its negative are considered for indicator analysis. Default is 0.025
- 'custom_changepoint_function_name': Name of the user-defined Python script for change point analysis. Default is empty string.
- 'custom_changepoint_function_script': Body of the the user-defined Python script for change point analysis. Default is empty string.
- 'chow_penalty': Penalty value used if the "operation_mode" is "chow". Default is 10.
- 'model': Name of the model for using Chow Test in false positive detection. Currently only 'l1' is supported. Default is 'l1'
-  'enableFillMissingDataWithLast': If enabled, the system fills the missing samples with the last measure. This is independent of your "aggregation_type". Default is False.
-  
The timeseries processing has stand-alone core docker options explained below.

## Building the "run_cython.pyx" Cython file
NOTE THAT: The container already includes a compiled version of the Cython code. No need to do this step unless you have changed the .pyx.
* Install the required packages (setuptools, Cython and NumPy) through pip.
* Run the command to cythonize the "run_cython.pyx" file
<pre>python setup.py build_ext --inplace</pre>
* After building, "run_cython.c" and "run_cython.cpython-36m-x86_64-linux-gnu.so" files will be created.
* File with the ".so" extension is importable from Python files.
* Run the "test_cython.py" file to call an imported Cython function from Python file.
<pre>python test_cython.py</pre>


## Docker reference

### Standalone deployment
* There must be a running redistimeseries app on the local host port 6379.
If there isn't one, deploy with docker quickly:
<pre>docker run -dp 6379:6379 -it --rm redislabs/redistimeseries</pre>

* Change directory to project root:
<pre>cd MAGI/TimeSeries</pre>

* Build the time series core docker image with command below,
don't forget dot at the end which indicates the current directory:
<pre>docker build -t time-series-core .</pre>

* Browse env_files/.env-core file to look at environment variables. 
Update the file as your needs.

* Start time series core app container with environment file:
<pre>docker run -d --name=time-series-core-app --env-file env_files/.env-core --net=host -it time-series-core</pre>


