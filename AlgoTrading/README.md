## TradingDataSourceService - AlgoTradingService

### TradingDataSourceService

* Browse to AlgoTrading folder and build trading-data-source image. 
  
<pre>cd MAGI/AlgoTrading</pre>
<pre>docker build -t trading-data-source .</pre>

* Start the DataSource container from MAGI MaC API with the "start_live_streaming_data_source" or "start_historical_data_source" methods

### Before running, create SSH tunnels to get the required data (news and stock data)
* Run below command
<pre>ssh -nNT -L 6381:localhost:6381 -L 6380:localhost:6380 username@66.159.49.92 -p 9002</pre>