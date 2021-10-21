## Docker reference


### Cluster Deployment

* Browse to TimeSeries folder and build times-series-core image. 
  
<pre>cd MAGI/TimeSeries</pre>
  
<pre>docker build -t time-series-core .</pre>

* Change directory to project root:

<pre>cd MAGI/MagiMonitoring</pre>

* Check the docker compose configuration in the docker-compose.yml file to see details.

* Browse env_files/.env-api to look at the environment variables. Update the parameters in the file as your needs.

* Deployment:
<pre>sudo chmod 777 start.sh</pre>
<pre>./start.sh</pre>

* Browse http://localhost:8000/docs to view and call API methods.

### Run time series scheduler job 
After done upper instructions, 
* Check http://localhost:5000/ is alive. (This is MagiFinance web project.)
    * If it is not alive, then you should open http://localhost:8000/docs and run /start_magi_web/ method with below parameters
    <pre>  {
            "magi_web_ui_port": 5000,
            "magi_web_mysql_port": 3306 
    }
   </pre>

* Run /register_time_series_job/ method from http://localhost:8000/docs with parameter "job_interval" = 10

### Run news scheduler job 
After done upper instructions, 
* Check http://localhost:5000/ is alive. (This is MagiFinance web project.)
    * If it is not alive, then you should open http://localhost:8000/docs and run /start_magi_web/ method with below parameters
    <pre>  {
            "magi_web_ui_port": 5000,
            "magi_web_mysql_port": 3306 
    }
   </pre>

* Run /register_news_job/ method from http://localhost:8000/docs with parameter "job_start_hour": "05","job_start_minute": "30"


