# -*- coding: utf-8 -*-
"""
MAGI TimeSeries Analysis Main Functionality
"""
import pickle

from timeSeriesFunctions import TimeSeriesFunctions, MPFlossLoop
import timeSeriesFunctions
import time
import matplotlib.pyplot as plt
import pandas as pd
import timeSeriesL1Analytics
from redis import Redis
from redistimeseries.client import Client
import json
from distutils import util


class TimeSeriesOperations:
    def __init__(self, redis_host: str, redis_port: int, output_redis_host: str, output_redis_port: int):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.output_redis_host = output_redis_host
        self.output_redis_port = output_redis_port
        self.redis_client = Redis(host=self.redis_host, port=self.redis_port)
        self.redis_output_client = Redis(host=self.output_redis_host, port=self.output_redis_port,
                                         decode_responses=True)
        self.redis_timeseries_client = Client(host=self.redis_host, port=self.redis_port)
        self.redis_timeseries_output_client = Client(host=self.output_redis_host, port=self.output_redis_port)
        self.time_series_functions = TimeSeriesFunctions(self.redis_host, self.redis_port)

    def analyze_time_series_csv(self,
                                df,
                                from_time: int,
                                to_time: int,
                                aggregation_type: str,
                                bucket_size_msec: int,
                                num_regimes: int,
                                filters: str,
                                ts_freq_threshold: int,
                                peek_ratio: float,
                                enablePlotting: bool,
                                enablePrediction: bool,
                                enablePercentChange: bool,
                                window: int,
                                timeZone: str,
                                output_name: str,
                                process_period: int,
                                enableBatch: bool,
                                miniBatchTimeWindow: int,
                                miniBatchSize: int,
                                enableStreaming: bool,
                                operation_mode: str,
                                percent_change_event_ratio: float,
                                percent_change_indicator_ratio: float,
                                custom_changepoint_function_name: str,
                                custom_changepoint_function_script: str,
                                chow_penalty: int,
                                model: str,
                                enableFillMissingDataWithLast: bool):

        labels = {}
        for item1 in filters.split(","):
            key_val_list = item1.split("=")
            labels[key_val_list[0]] = key_val_list[1]

        self.time_series_functions.loadDataFrameToRedis(df, labels)
        self.process_time_series(from_time,
                                 to_time,
                                 aggregation_type,
                                 bucket_size_msec,
                                 num_regimes,
                                 filters,
                                 ts_freq_threshold,
                                 peek_ratio,
                                 enablePlotting,
                                 enablePrediction,
                                 enablePercentChange,
                                 window,
                                 timeZone,
                                 output_name,
                                 process_period,
                                 enableBatch,
                                 miniBatchTimeWindow,
                                 miniBatchSize,
                                 enableStreaming,
                                 operation_mode,
                                 percent_change_event_ratio,
                                 percent_change_indicator_ratio,
                                 custom_changepoint_function_name,
                                 custom_changepoint_function_script,
                                 chow_penalty,
                                 model,
                                 enableFillMissingDataWithLast)

    def insert_data_to_db(self, csv_file_path: str, labels: dict):
        print("Inserting data to db...")
        self.time_series_functions.loadDataToRedis(fname=csv_file_path,
                                                   labels=labels)
        # labels={"TARGET": "SENSORDOG"})
        print("Done.")

    def process_time_series(self,
                            from_time: int,
                            to_time: int,
                            aggregation_type: str,
                            bucket_size_msec: int,
                            num_regimes: int,
                            filters: str,
                            ts_freq_threshold: int,
                            peek_ratio: float,
                            enablePlotting: bool,
                            enablePrediction: bool,
                            enablePercentChange: bool,
                            window: int,
                            timeZone: str,
                            output_name: str,
                            process_period: int,
                            enableBatch: bool,
                            miniBatchTimeWindow: int,
                            miniBatchSize: int,
                            enableStreaming: bool,
                            operation_mode: str,
                            percent_change_event_ratio: float,
                            percent_change_indicator_ratio: float,
                            custom_changepoint_function_name: str,
                            custom_changepoint_function_script: str,
                            chow_penalty: int,
                            model: str,
                            enableFillMissingDataWithLast: bool):
        import uuid
        print(f"Input Target Filter: {filters}")
        print(f"Output Target Filter: {output_name}")

        filters = filters.split(",")
        plots = {}
        last_ts_streamed = 0
        params = {"from_time": from_time,
                  "to_time": to_time,
                  "aggregation_type": aggregation_type,
                  "bucket_size_msec": bucket_size_msec,
                  "num_regimes": num_regimes,
                  "filters": filters,
                  "ts_freq_threshold": ts_freq_threshold,
                  "peek_ratio": peek_ratio,
                  "enablePlotting": enablePlotting,
                  "enablePrediction": enablePrediction,
                  "enablePercentChange": enablePercentChange,
                  "window": window,
                  "timeZone": timeZone,
                  "output_name": output_name,
                  "process_period": process_period,
                  "enableBatch": enableBatch,
                  "miniBatchTimeWindow": miniBatchTimeWindow,
                  "miniBatchSize": miniBatchSize,
                  "enableStreaming": enableStreaming, "operation_mode": operation_mode,
                  "percent_change_event_ratio": percent_change_event_ratio,
                  "percent_change_indicator_ratio": percent_change_indicator_ratio,
                  "custom_changepoint_function_name": custom_changepoint_function_name,
                  "custom_changepoint_function_script": custom_changepoint_function_script,
                  "chow_penalty": chow_penalty, "model": model,
                  "enableFillMissingDataWithLast": enableFillMissingDataWithLast}

        guid = 'SensorDog:param:killLoop:' + str(uuid.uuid4())
        if enableStreaming or enableBatch:
            print("enableStreaming or enableBatch is True. \n Creating/setting", guid,
                  "= False on output Redis. Set it to True to kill this process after the current loop.")
            _ = self.redis_output_client.set(guid, "False")
        loop_no = 0
        while True:
            # Check if Redis is up
            all_regimes = []
            if not self.redis_client.ping():
                print("Unable to reach redis timeseries at", self.redis_host, self.redis_port)
                return True
            start = time.time()
            # read time series from Redis
            if not enableStreaming:
                all_data = self.time_series_functions.getDataFromRedis(from_time=from_time,
                                                                       to_time=to_time,
                                                                       aggregation_type=aggregation_type,
                                                                       bucket_size_msec=bucket_size_msec,
                                                                       filters=filters,
                                                                       enablePercentChange=enablePercentChange,
                                                                       window=window)
            else:
                to_time = from_time - (miniBatchSize - 1) * bucket_size_msec
                all_data = self.time_series_functions.getDataFromRedis(from_time=from_time,
                                                                       to_time=to_time,
                                                                       aggregation_type=aggregation_type,
                                                                       bucket_size_msec=bucket_size_msec,
                                                                       filters=filters,
                                                                       enablePercentChange=enablePercentChange,
                                                                       window=window)
            # sampling rate control
            if len(all_data) > 0:
                loop_no = loop_no + 1 
                sampling_list = max(all_data["ts_all"], key=len)
                if len(sampling_list) < miniBatchSize:
                    print(
                        "the length of the longest timeseries is shorter than the minibatch size. Check input parameters.")
                    return True
                sampling_list = [x for x in sampling_list if type(x) in [int, float]]
                if len(sampling_list) >= 2:
                    sampling_list = [y - x for x, y in zip(sampling_list[:-1], sampling_list[1:])]
                    sampling_rate = min(sampling_list)
                else:
                    sampling_rate = -1
                if sampling_rate > bucket_size_msec:
                    print(sampling_rate, "ms sampling rate is greater than", bucket_size_msec,
                          "ms bucket size\n Terminating...")
                    return True
            else:  # nothing to process
                print("No data retrieved from Redis. Terminating...")
                return True
            if (not enableStreaming) or \
                    (enableStreaming and (
                            all_data["ts_max"] >= (last_ts_streamed + miniBatchTimeWindow * bucket_size_msec))):
                df = pd.DataFrame(all_data["df"])
                # Filter less interesting signals out
                df, df_lines, df_squares, df_spikes, all_data["ts_all"] = self.time_series_functions.clusterTs(df,
                                                                                                               all_data[
                                                                                                                   "ts_all"])
                # Get regime changes and their histogram
                if len(df) > 0:
                    if enableFillMissingDataWithLast:
                        df = df.fillna(method='ffill')
                    if enablePercentChange:
                        df = df.pct_change(window)
                        df = df.fillna(0)

                    if operation_mode.lower() != 'pct':  # MP, CHOW and CUSTOM
                        if operation_mode.lower() == 'mp':
                            all_regimes = self.time_series_functions.getRegimesFromMP(df,
                                                                                      num_regimes=num_regimes,
                                                                                      window=window)
                            df_all_regimes = pd.DataFrame(all_regimes)
                            histogram = timeSeriesL1Analytics.getHistogramFromUnalignedDf(df_all_regimes,
                                                                                          all_data["ts_all"],
                                                                                          all_data["ts_min"],
                                                                                          all_data["ts_max"],
                                                                                          bucket_size_msec)

                        elif operation_mode.lower() == 'chow':
                            all_regimes = self.time_series_functions.getRegimesFromChow(df,
                                                                                        model=model,
                                                                                        chow_penalty=chow_penalty)
                            histogram = timeSeriesL1Analytics.getHistogramFromUnalignedDf(pd.DataFrame(all_regimes),
                                                                                          all_data["ts_all"],
                                                                                          all_data["ts_min"],
                                                                                          all_data["ts_max"],
                                                                                          bucket_size_msec)
                        elif operation_mode.lower() == 'custom':
                            try:
                                exec(custom_changepoint_function_script)
                                all_regimes = custom_changepoint_function_name(df)
                                histogram = timeSeriesL1Analytics.getHistogramFromUnalignedDf(
                                    pd.DataFrame(all_regimes),
                                    all_data["ts_all"],
                                    all_data["ts_min"],
                                    all_data["ts_max"],
                                    bucket_size_msec)
                            except Exception as e:
                                print(e)
                                print("Custom script has errors.\n Terminating the job.")
                                return True

                        # Plot histogram of regime changes
                        if enablePlotting:
                            plt.figure(0)
                            plt.title("Histogram of Regime Changes")
                            plt.plot(histogram)
                            base64_histogram = self.time_series_functions.get_current_plot_as_base64()
                            plots['histogram'] = base64_histogram

                        events = timeSeriesL1Analytics.getCandidateEvents(histogram, len(histogram),
                                                                          ts_freq_threshold,
                                                                          peek_ratio,
                                                                          sampling_rate=bucket_size_msec)
                        # Plot events on the histogram
                        if enablePlotting:
                            plt.figure(1)
                            plt.title("Histogram of Events")
                            self.time_series_functions.plotEventsOnHistogram(histogram, len(histogram), events)
                            base64_events = self.time_series_functions.get_current_plot_as_base64()
                            plots['events'] = base64_events
                        # get indicators
                        indicators = self.time_series_functions.getIndicators(events, df, all_regimes)

                    else:  # PCT
                        events, indicators, all_regimes, plots['normalized_increase'], plots[
                            'normalized_decrease'] = self.time_series_functions.getIndicatorsEventsPct(df,
                                                                                                       window,
                                                                                                       percent_change_event_ratio,
                                                                                                       percent_change_indicator_ratio,
                                                                                                       enablePlotting)

                    # print event stats
                    self.time_series_functions.printEventStats(
                        list(range(all_data["ts_min"], all_data["ts_max"] + bucket_size_msec, bucket_size_msec)),
                        indicators, events, timeZone)
                    # Get predictive powers and generate correlations from a model
                    df_event_contributor = pd.DataFrame()
                    if not enablePrediction:
                        # df_event_contributor = self.time_series_functions.getBestPredictiveModel(events, df,
                        #                                                                         all_regimes)
                        df_event_contributor = self.time_series_functions.getPredictiveModelContributions(events,
                                                                                                          df,
                                                                                                          all_regimes)

                        # if len(df_event_contributor) > 0:
                        #     df_plotly = df[list(df_event_contributor['li name'].values)].copy()
                        #     self.time_series_functions.generateCorrelations(df_plotly, enablePlotting"])
                    # generate output
                    end_time = time.time()
                    if self.redis_output_client.ping():
                        print("Converting regime change locations to time stamp...")
                        all_regimes = self.time_series_functions.regimes2timestamps(all_regimes, bucket_size_msec,
                                                                                    all_data["ts_min"])
                        dict_events = self.time_series_functions.indicators2datetime(events.to_dict(),bucket_size_msec, all_data["ts_min"], timeZone)
                        output_data = {'events': dict_events, 'indicators': indicators.to_dict(),
                                       'contributors': df_event_contributor.to_dict(), "all_regimes": all_regimes,
                                       "plots": plots,
                                       "Analyzed": df.columns.tolist(),
                                       "Line": df_lines.columns.tolist(),
                                       "Spike": df_spikes.columns.tolist(),
                                       "Square": df_squares.columns.tolist(),
                                       "df_data": all_data["df"].to_json(),
                                       "metadata": {"parameters": params, "start_ts": start, "end_ts": end_time,
                                                    "min_ts": all_data["ts_min"], "max_ts": all_data["ts_max"],"ts_all":all_data["ts_all"], "loop_no":loop_no}}
                        output_data = json.dumps(output_data)
                        _ = self.redis_output_client.xadd(output_name, {'data': output_data})
                        _ = self.redis_output_client.execute_command("save")
                    else:
                        print("Unable to reach redis for output at", self.output_redis_host,
                              self.output_redis_port)
                        return True
                    # Create dynamic dashboards
                    if enablePlotting:
                        self.time_series_functions.createDashBoards(events, indicators, df_event_contributor,
                                                                    all_data["ts_all"][0])
                else:  # No data with regime changes. Line, Spike, Square signals only
                    end_time = time.time()
                    if self.redis_output_client.ping():
                        output_data = {'events': {}, 'indicators': {},
                                       'contributors': {}, "all_regimes": [],
                                       "plots": {},
                                       "Analyzed": df.columns.tolist(),
                                       "Line": df_lines.columns.tolist(),
                                       "Spike": df_spikes.columns.tolist(),
                                       "Square": df_squares.columns.tolist(),
                                       "df_data": all_data["df"].to_json(),
                                       "metadata": {"parameters": params, "start_ts": start, "end_ts": end_time,
                                                    "min_ts": all_data["ts_min"], "max_ts": all_data["ts_max"],
                                                    "loop_no": loop_no}}
                        output_data = json.dumps(output_data)
                        _ = self.redis_output_client.xadd(output_name, {'data': output_data})
                        _ = self.redis_output_client.execute_command("save")
                    else:
                        print("Unable to reach redis for output at", self.output_redis_host,
                              self.output_redis_port)
                        return True #Terminate if no redis


                print("MAGI TimeSeries Analysis completed in total of ", round(end_time - start, 2),
                      "sec.")

                if enableBatch:
                    print("Sleeping till the next loop for loop sec=", process_period)
                    time.sleep(process_period)
                elif not enableStreaming:
                    return True
                else:
                    last_ts_streamed = all_data["ts_max"]
                if enableBatch or enableStreaming:
                    plt.close("all")
                    if self.redis_output_client.exists(guid):
                        killLoop = bool(
                            # util.strtobool(self.redis_output_client.get(guid).decode('utf-8')))
                            util.strtobool(self.redis_output_client.get(guid)))
                        if killLoop:
                            print("kill signal received. Terminating...")
                            _ = self.redis_output_client.delete(guid)
                            return True
                        else:
                            print(guid, "is False. Starting again")
        return True

    def monitorOnlineTimeSeries(self,
                                ts_list,
                                from_time,
                                to_time,
                                operation_mode,
                                aggregation_type,
                                bucket_size_msec,
                                chow_penalty,
                                percent_change_threshold,
                                percent_window,
                                stream_refresh_rate,
                                subsequenceLength,
                                windowSize,
                                excl_factor,
                                n_regimes,
                                last_minutes_count,
                                refresh_interval,
                                dashboard_title):
        import threading
        try:
            if self.redis_client.ping():
                if operation_mode == "mp":
                    ts_names = ts_list.split(",")
                    created_streaming_dashboard_id, dashboard_name, panel_ids = timeSeriesFunctions.create_streaming_dashboard_on_grafana(
                        ts_names, dashboard_title, last_minutes_count, refresh_interval)
                    if panel_ids is not None:
                        if len(panel_ids) > 0:
                            i = 0
                            for pids in panel_ids:
                                print("Starting online monitoring thread for stream: ", ts_names[i])
                                thr = threading.Thread(target=MPFlossLoop, args=(
                                    self.redis_timeseries_client, created_streaming_dashboard_id,
                                    pids,
                                    ts_names[i], from_time, to_time,
                                    stream_refresh_rate, aggregation_type,
                                    bucket_size_msec, windowSize, n_regimes, excl_factor,
                                    subsequenceLength))
                                i = i + 1
                                thr.start()
                                print("done")
                else:
                    print("Only mp='matrix profile' implemented for stream monitoring...")
                    return True
            else:
                print("unable to reach Redis...")
                return True
        except Exception as e:
            print(e)
            return True
