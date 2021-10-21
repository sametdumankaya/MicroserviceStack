# MSig : MAGI Signal Generator
MSig uses MAGI-timeseries core services including Matrix Profile or GainLoss Ratio to analyze any given set of time series to find events.

-- Install requirements.txt

-- Run "python setup.py install" for building cythonized Chow Test.

-- Start **MNews_Analyzer_start.py**  for news analysis once a day, and it sleeps until the next business day (sleeps over the weekend). Use a specific terminal or tmux session for this.

-- Start **MSig_start.py** for the event analysis for every period during the market hours. It sleeps for the next period. If the market is closes, it sleeps for the next business day. Use a specific terminal or tmux session for this.

### Brief overview of architecture:
-- MSig uses 3 Redis servers: The default port 6381 for reading live stock market data, 6380 to output MSig event results and parameters, 6378 is to put the MAGI indexes (e.g., industry-based gain-loss indexes) as timeseries.

-- MSig uses a mysql server at the port 3307 to save detected events.

-- MSig also reads 2 news queues (*NewsIndustry*, *NewsCompany*) at the port 6380. One queue for Company-based news, another one for Industry-based news. The queues contain news for each one of the companies or Industries starting from the closing time of the stock market on previous day to the opening time of the today's stock market. This process is a continuous loop performed by **MNews_Analyzer_start.py** using the rapidapi (https://rapidapi.com/). Each news' sentiment analysis is performed and their links are saved as a dataframe in the corresponding queue. When MSig detects a gain/loss event, it looks for a corresponding news to explain it.

-- MSig also checks during-the-day news per events. Each event's top contributer and the one with the highest market capital are used for during-the-day news analysis. NOTE THAT WE ARE LIMITED TO 100K rapidapi calls per month.

-- **MSig_start.py** parameters can be changed without restarting the main loop. They are saved in the Redis at 6380. If you directly alter them, the loop will use the new parameters in the next iteration. Please read the variables carefully before changing them. 

### MSig Parameters:  
--**period** (default=600): perid of signal processing in sec. 

--**L2fileName** (default='finL2Extension.graphml'): Name of the graphml L2 extension file that includies companies, tickers, sectors, etc. 

--**redis_host** (default='localhost'): Redis host for input time series.

--**redis_host** (default=6381): Redis port for input time series.

--**msig_host** (default='localhost'): Redis host for signal output AND dynamic parameter changing.

--**msig_port** (default=6380): Redis port for signal output AND dynamic parameter changing.

--**mind_host** (default='localhost'): Redis host for index output (gain/loss based industry indices).

--**mind_port** (default=6378): Redis port for index output (gain/loss based industry indices).

--**from_time** (default=0): End of data analysis interval for time series @ port 6381. This is the larger one. 0 means now.

--**to_time** (default=-1): Start of data analysis interval for time series @ port 6381. This is the smaller one. -1 means starting from any time.

--**prefix** (default='rts1:01:'): Rrefix of the keys of interest on Redis @ port 6381.

--**aggregation_type** (default='last'): Time series aggregation type (min, max, avg, first, last...) for Redis @ port 6381.

--**bucket_size_msec** (default=60000): Aggregation bucket size in msec for time series for Redis @ port 6381.

--**num_regimes** (default=20): Max number of semantic segmentation per time series for Matrix Profile algorithm.

--**window_size** (default=10): Window size for semantic segmentation of time series for MP. When MP disabled, this is the parameter for percent-change-based gain and loss index. The window size is attached to the index name in MInd Redis.

--**last_batch_control_variable** (default='mac_simlooping'): 'This variable marks if the current batch is the last batch for simulating data that loops itself. Not used for live data processing.

--**filters** (default="SYMSET=ACTIVE"): Filtering labels for Redis mrange bulk reading. If you want your data to be processed, make sure you use this label in Redis too.

--**ts_freq_threshold** (default=20): Threshold value for number of simultaneous regime changes for event detection.

--**num_regimes** (default=20): Max number of semantic segmentation per time series for Matrix Profile algorithm.

--**peek_ratio** (default=0.30): Threshold value for peeks on histogram for event detection. The tallest histogram item and anything that is greater than equal to peek_ratioXtallest item will be considered as events. This is used by Matrix Profile algorithm.

--**enablePlotting** (default=False): Enable plotting of histograms and events.

--**killMSig** (default=False): This a signal to kill MSig. Set it to True if you want to send a kill signal to MSig.

--**enableSectorIndustry** (default=True): Enable sector and industry-based anaysis of events.

--**enablePrediction** (default=False): Enable prediction based on event analysis. If set True, MSig will push its results to MSig Redis as stream continouously. The name of the output stream is *MSIG_OUTPUT*.

--**enableNewsGeneration** (default=True): Enable news generation based on event analysis. When enabled, each loop sends data to the front end.

--**saveToMysql** (default=True): Enable to save session info and events to MYSql.

--**mysql_port** (default=3307): MySql port for signal output.

--**mysql_host** (default='127.0.0.1'): MySql host for signal output.

--**mysql_user** (default='root'): MySql user for signal output.

--**mysql_pass** (default=MSIG_MYSQL_PASS): Environment variable's name for Mysql password used for signal outputing. Default is set to the environment variable $MSIG_MYSQL_PASS (https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/ ).

--**enableMP** (default=False): Enable using Matrix Profile based event generation. When disabled, gain loss indices are used.

--**enableCorrelations** (default=True): Enable pushing correlation plots to the front end. Event correlations are pushed at each computation. Industries are too. Note that this is a parallel thread. Make sure this thread sends a '(THREAD):Done' signal before you kill MSig main loop.

--**gainLossEventRatio** (default=0.05): If a peak's height is grater/smaller than this ratio, it is an event. Any normalized peak in gain/loss signal smaller than this value will be ignored as an event. 

--**gainLossIndicatorThreshold** (default=0.025): If a company's gain/loss is larger/smaller than this ratio, it is an indicator of that event. Any company's gain/loss signal smaller than this value will be ignored as an indicator. Note that since volume gain/loss indices flactuates a lot, MSig doubles this threashold continually to keep the max number of indicators belowe 40.

--**timeZone** (default='US/Pacific'): Time zone of the context.

--**curatedNews** (default='USA Political, Bitcoin, Covid-19'): Comma separated topics for news analysis. Max 10 topics and 5 News per topic are allowed.

### Structure of the MSig Data at Redis 6380 as Redis Stream (https://redis.io/topics/streams-intro)
--bucket_size_msec: integer value for aggregation bucket size 

--event_price_ids: mysql ids of the price events detected 

--event_volume_ids: mysql ids of the volume events detected 

--events_price: data frame holding price events' li, mi, ti time stamps. 

--events_volume:data frame holding volume events' li, mi, ti time stamps. 

--price_columns: names companies in the same order with the price data columns 

--regimes_price: data frame holding regime change histogram of price data. The regime change on the ith row belongs to the ith company name in the price_columns 

--regimes_volume: data frame holding regime change histogram of volume data. The regime change on the ith row belongs to the ith company name in the volume_columns 

--ts_price_max: the largest time stamp in msec of price data. 

--ts_price_min: the smallest time stamp in msec of price data. The total number of  price data samples =( ts_price_max - ts_price_min) / bucket_size_msec 

--ts_volume_max: the largest time stamp in msec of volume data. 

--ts_volume_min: the smallest time stamp in msec of volume data. The total number of  volume data samples =( ts_volume_max - ts_volume_min) / bucket_size_msec 
