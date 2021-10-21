from redistimeseries.client import Client
import time
import pandas as pd
import timeSeriesL1Analytics
import matrixprofile as mp
import matplotlib.pyplot as plt
from scipy import interpolate
import numpy as np
import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
from scipy.signal import find_peaks, peak_prominences
import io
import urllib
import base64
import run_cython
import requests
import stumpy
from numba import cuda
import copy
import pytz
from xgboost import XGBClassifier


def MPFlossLoop(rts, dashboard_id, panel_id, ts_name, from_time=0, to_time=-1, stream_refresh_rate=10,
                aggregation_type='last', bucket_size_msec=1000, windowSize=10, n_regimes=2, excl_factor=5,
                subsequenceLength=10,threshold=0.5):
    try:
        all_gpu_devices = [device.id for device in cuda.list_devices()]
    except cuda.CudaSupportError:
        all_gpu_devices = []

    try:
        # read entire data for annotation
        outp = rts.range(ts_name, from_time=from_time, to_time=to_time, aggregation_type=aggregation_type,
                         bucket_size_msec=bucket_size_msec)
        ts = []
        data = []
        if len(outp) > 0:
            ts, data = map(list, zip(*outp))
        if len(all_gpu_devices) > 0:
            mp = stumpy.gpu_stump(data, m=windowSize, device_id=all_gpu_devices)
        else:
            mp = stumpy.stump(data, m=windowSize)

        cac, regime_locations = stumpy.fluss(mp[:, 1], L=subsequenceLength, n_regimes=n_regimes,
                                             excl_factor=excl_factor)
        # send the first regime locations:
        regime_ts = []
        regime_descs = []
        regime_locations = list(regime_locations)
        for i in regime_locations:
            regime_ts.append(ts[i])
            regime_descs.append("Regime Change")
        print("regime locations:", regime_locations)
        annotation_result = add_annotation_to_panel(dashboard_id, panel_id, regime_ts, regime_descs)

        # Create stream
        stream = stumpy.floss(mp, data, m=windowSize, L=subsequenceLength, excl_factor=excl_factor)
        while True:  # infinite annotation loop
            from_time = max(ts)  # last time stamp processed
            while True:  # stream size control loop
                NewOutP = rts.range(ts_name, from_time=from_time, to_time=-1, aggregation_type=aggregation_type,
                                    bucket_size_msec=bucket_size_msec)
                ts = []
                data = []
                if len(NewOutP) > 0:
                    ts, data = map(list, zip(*NewOutP))
                if len(NewOutP) >= len(outp) + stream_refresh_rate:
                    break
            for i, t in enumerate(data):
                stream.update(t)
            regime_locations = get_regimes_threshold_cac(cac=stream.cac_1d_, 
                                                         threshold=threshold, 
                                                         windowSize=windowSize, 
                                                         excl_factor=excl_factor)
            regime_ts = []
            regime_descs = []
            regime_locations = list(regime_locations)
            # remove false positives
            #regime_locations = [l for l in regime_locations if l % subsequenceLength != 0]
            for i in regime_locations:
                regime_ts.append(ts[i])
                regime_descs.append("Regime Change")
            print("regime locations:", regime_locations)
            annotation_result = add_annotation_to_panel(dashboard_id, panel_id, regime_ts, regime_descs)
            outp = NewOutP
    except Exception as e:
        print(e)
        return True


def get_regimes_threshold_cac(cac, threshold=0.5, windowSize=10, excl_factor=5):
    ez=windowSize*excl_factor
    tmp=np.copy(cac)
    regime_locs=[]
    n=len(tmp)
    while True:
        min_index = np.argmin(tmp)
        if tmp[min_index]>=threshold:
            break
        else:
            regime_locs.append(min_index)
            ez_start = np.max([0, min_index - ez])
            ez_end = np.min([n, min_index + ez])
            tmp[ez_start:ez_end] = 1
    return regime_locs


def create_streaming_dashboard_on_grafana(streaming_time_series_names, title, last_minutes_count, refresh_interval):
    response = requests.post("http://localhost:8001/create_streaming_timeseries_graphs/", json={
        "streaming_time_series_info_list": [{
            "time_series_name": streaming_time_series_names[i]
        } for i in range(len(streaming_time_series_names))],
        "title": title,
        "last_minutes_count": int(last_minutes_count),
        "refresh_interval": refresh_interval  # 1s, 5s, 3m
    }).json()
    created_streaming_dashboard_id = response["created_streaming_dashboard_id"]
    dashboard_name = response["dashboard_name"]
    panel_ids = response["panel_ids"]
    return created_streaming_dashboard_id, dashboard_name, panel_ids


def add_annotation_to_panel(dashboard_id, panel_id, timestamps, descriptions):
    response = requests.post("http://localhost:8001/add_annotations/", json={
        "dashboard_id": int(dashboard_id),
        "panel_id": int(panel_id),
        "annotations": [{
            "time_stamp": timestamps[i],
            "description": descriptions[i]
        } for i in range(len(timestamps))]
    }).json()
    return response  # True or False as bool


class TimeSeriesFunctions:
    def __init__(self, host, port):
        np.warnings.filterwarnings('ignore')
        self.host = host
        self.port = port
        self.redis_timeseries_client = Client(self.host, self.port)

    def loadDataFrameToRedis(self, df, labels: dict):
        timeStamps = df.iloc[:, 0].values.astype(float)
        timeStamps = [int(x) for x in timeStamps]
        for i in range(1, len(df.columns)):
            # ts_name='ts'+str(i)
            ts_name = df.columns[i]
            # Create time series
            try:
                _ = self.redis_timeseries_client.create(ts_name, labels=labels)
            except:
                _ = self.redis_timeseries_client.execute_command("del " + ts_name)
                _ = self.redis_timeseries_client.create(ts_name, labels=labels)
            # Create array of key, ts, value tuples
            arr_ktv = tuple(zip(timeStamps, df.iloc[:, i].values.astype(float)))
            arr_ktv = [(ts_name,) + xs for xs in arr_ktv]
            _ = self.redis_timeseries_client.madd(arr_ktv)
        _ = self.redis_timeseries_client.execute_command("save")
        return

    def loadDataToRedis(self, fname: str, labels: dict):
        df = pd.read_csv(fname)
        timeStamps = df.iloc[:, 0].values.astype(float)
        timeStamps = [int(x) for x in timeStamps]
        for i in range(1, len(df.columns)):
            # ts_name='ts'+str(i)
            ts_name = df.columns[i]
            # Create time series
            try:
                _ = self.redis_timeseries_client.create(ts_name, labels=labels)
            except:
                _ = self.redis_timeseries_client.execute_command("del " + ts_name)
                _ = self.redis_timeseries_client.create(ts_name, labels=labels)
            # Create array of key, ts, value tuples
            arr_ktv = tuple(zip(timeStamps, df.iloc[:, i].values.astype(float)))
            arr_ktv = [(ts_name,) + xs for xs in arr_ktv]
            _ = self.redis_timeseries_client.madd(arr_ktv)
        _ = self.redis_timeseries_client.execute_command("save")
        return

    def streamDataFrameToRedis(self, df, labels: dict, isMilliSeconds=True):
        print("Streaming data into redis for simulation")
        tsNames = []
        df = df.drop(['ts'], axis=1)
        ms2mc = 1
        if isMilliSeconds:
            ms2mc = 1000
        # Delete the existing ts
        for i in range(1, len(df.columns)):
            ts_label = str(df.columns[i])
            ts_name = ts_name = 'ts' + str(i)
            try:
                self.redis_timeseries_client.create(ts_name, labels=labels)
                tsNames.append(ts_name)
            except:
                self.redis_timeseries_client.delete(ts_name)
                self.redis_timeseries_client.create(ts_name, labels=labels)
                tsNames.append(ts_name)
        while True:
            for i in range(len(df)):
                data = df.iloc[i, :].values.astype(float)
                timestamps = [round(time.time() * ms2mc)] * len(data)
                merged_data = list(zip(tsNames, timestamps, data))
                _ = self.redis_timeseries_client.madd(merged_data)

    def getDataFromRedis(self, from_time=0, to_time=-1, aggregation_type="last", bucket_size_msec=60000,
                         filters=["TARGET=SENSORDOG"], enablePercentChange=True, window=2):
        ts_min = []
        ts_max = []
        ts_all = []
        data_all = []
        keys_all = []
        try:
            print("Querying from Redis database...")
            start = time.time()
            bulk_data = self.redis_timeseries_client.mrange(from_time=from_time,
                                                            to_time=to_time,
                                                            aggregation_type=aggregation_type,
                                                            bucket_size_msec=bucket_size_msec,
                                                            filters=filters)
            print(round(time.time() - start, 2), "sec for retrieving", len(bulk_data), "time series")
            print("Preparing dataframe from query result...")
            for d in bulk_data:
                key = str(list(d.keys())[0])  # name of time series
                rest = list(d.get(key))[1]
                if len(rest) > 0:
                    ts, data = map(list, zip(*rest))  # timestamps and data 
                    ts_min.extend(ts)
                    ts_min = [min(ts_min)]
                    ts_max.extend(ts)
                    ts_max = [max(ts_max)]
                    ts_all.append(ts)
                    data_all.append(data)
                    keys_all.append(key)
            print("Done")
            df = pd.DataFrame(data_all)
            df = df.transpose(copy=True)
            df.columns = keys_all
            # if enablePercentChange:
            #     df = df.pct_change(window-1)
            #     df = df[window-1:]
            #     for i in range(len(ts_all)):
            #         ts_all[i]=ts_all[i][window-1:]
            #
            #     #for l in ts_all:
            #     #    del l[0]
            #     ts_min = [min(map(min, ts_all))]
            #     ts_max = [max(map(max, ts_all))]
            all_data = {"ts_all": ts_all, "df": df, "ts_min": ts_min[0], "ts_max": ts_max[0]}
            return all_data
        except Exception as e:
            print(e)
            return {}

    def clusterTs(self, df, ts_all):
        """
        This function receives a data frame of time series. Analyzes them and returns initial clusters:
            lines - constant slope time series are not interesting
            squares - stair-like square signals dont look like contributing to events
            spikes - spike like signal can be event triggers. Need further analysis.
        """
        df_lines = pd.DataFrame()
        df_spquares = pd.DataFrame()
        df_spikes = pd.DataFrame()
        df_tmp = pd.DataFrame(df)
        try:
            start = time.time()
            print("Filtering lines, squares and spikes from time series")
            df_tmp, df_lines = timeSeriesL1Analytics.filter_lines(df_tmp)
            df_tmp, df_spikes = timeSeriesL1Analytics.filter_spikes(df_tmp)
            df_spquares, df_spikes = timeSeriesL1Analytics.splitSquaresFromSpikes(df_spikes)
            print(int(time.time() - start), "sec. for successfully filtering")
        except Exception as e:
            print(e)
        ts_tmp = []
        col_eliminated = []
        col_eliminated.append(df_lines.columns.tolist())
        col_eliminated.append(df_spikes.columns.tolist())
        col_eliminated.append(df_spquares.columns.tolist())
        col_eliminated = [item for x in col_eliminated for item in x]

        index_eliminated = []  # index to be eliminated
        for i in range(len(df.columns.tolist())):
            if df.columns.tolist()[i] in col_eliminated:
                index_eliminated.append(i)

        for i in range(len(ts_all)):
            if i not in index_eliminated:
                ts_tmp.append(ts_all[i])
        df = pd.DataFrame(df_tmp)
        df = df.reset_index(drop=True)
        df_lines = df_lines.reset_index(drop=True)
        df_spquares = df_spquares.reset_index(drop=True)
        df_spikes = df_spikes.reset_index(drop=True)
        return df, df_lines, df_spquares, df_spikes, ts_tmp

    def getRegimesFromMP(self, df, num_regimes=20, window=10, isRemoveFirstFalsePositive=False):
        """This function receives a df of time series. Uses matrix profiles to find regime changes.
        Creates a histogram form the regime changes across all time series"""

        # Matrix profile
        timings_mp = []
        timings_fluss = []
        all_regimes = []
        print("Running matrix profile to get regime changes...")
        start_all = time.time()
        try:
            for i in range(len(df.columns)):
                ts = df.iloc[:, i]
                ts = ts[ts.notnull()].values.astype('float')
                start_time = time.time()
                profile = mp.compute(ts, windows=[window], n_jobs=-1)
                timings_mp.append(time.time() - start_time)
                start_time = time.time()
                x = mp.discover.regimes(profile, num_regimes=num_regimes)
                timings_fluss.append(time.time() - start_time)
                regimes = list(filter(lambda x: x != 0, x["regimes"]))  # remove false positive at 0
                regimes = list(filter(lambda x: x != len(df), regimes))  # remove false positive at the end
                regimes = [int(x) for x in regimes]
                all_regimes.append(regimes)
        except Exception as e:
            print(e)

        print(round(time.time() - start_all, 2), "sec of total time....", round(sum(timings_mp), 2),
              " for MP computation,",
              round(sum(timings_fluss), 2), "for semantic seg")
        return all_regimes

    def plotEventsOnHistogram(self, histogram, number_of_samples, events):
        """This function viusalizes events on the histogram of regime changes"""
        plt.plot(histogram)
        for i, row in events.iterrows():
            start_event = row[0]
            end_event = row[2]
            peek = row[1]
            x = [start_event, peek, end_event]
            y = [0, histogram[peek], 0]
            x2 = np.linspace(x[0], x[-1], 1000)
            y2 = interpolate.pchip_interpolate(x, y, x2)
            plt.plot(x2, y2)
        plt.show()

    def printEventStats(self, time_stamps, indicators, events, timeZone='US/Pacific'):
        """This function prints the number of indicators per event & time stats"""
        # event stats
        tz = pytz.timezone(timeZone)
        date_time_stamps = [str(datetime.datetime.fromtimestamp(int(i / 1000)).astimezone(tz)) for i in time_stamps]
        # print(indicators)
        print("Event# \t #LeadingIndicatorCnt \t #MainIndicatorCnt \t #TrailingIndicatorCnt")
        for i, row in indicators.iterrows():
            print(i + 1, "\t", len(row["leading indicator"]), "\t", len(row["main indicator"]), "\t",
                  len(row["trailing indicator"]))
        # print(events)
        print("Event# \t #L.I.DateTime \t\t\t\t #M.I.DateTime \t\t\t\t #T.I.DateTime")
        for i, row in events.iterrows():
            if len(row) == 3:
                print(i + 1, "\t", date_time_stamps[int(row["leading indicator"])], "\t",
                      date_time_stamps[int(row["main indicator"])], "\t",
                      date_time_stamps[int(row["trailing indicator"])])
            else:
                print(i + 1, "\t", date_time_stamps[int(row["leading indicator"])], "\t",
                      date_time_stamps[int(row["main indicator"])], "\t",
                      date_time_stamps[int(row["trailing indicator"])], row["event type (percent change)"])

    def getIndicators(self, events, df, all_regimes):
        """Given events and a df of time series, this function creates df of indicators for each event"""
        ts_names = list(df.columns)
        mi = []
        li = []
        ti = []
        for i, r in events.iterrows():
            l = r["leading indicator"]
            m = r["main indicator"]
            t = r["trailing indicator"]
            tmp_l = []
            tmp_m = []
            tmp_t = []
            counter = 0
            for temp_r in all_regimes:
                if l in temp_r and ts_names[counter] not in tmp_l:
                    tmp_l.append(ts_names[counter])
                elif m in temp_r and ts_names[counter] not in tmp_m:
                    tmp_m.append(ts_names[counter])
                elif t in temp_r and ts_names[counter] not in tmp_t:
                    tmp_t.append(ts_names[counter])
                counter = counter + 1
            li.append(tmp_l)
            mi.append(tmp_m)
            ti.append(tmp_t)
        indicators = pd.DataFrame({"leading indicator": li, "main indicator": mi, "trailing indicator": ti})
        return indicators

    def getPredictiveModelContributions(self, events, df, all_regimes):
        # train a model
        df_regimes = pd.DataFrame(all_regimes)
        # Predictive power
        print("Preparing the dataset for training")
        start = time.time()
        cols = list(df.columns)
        cols.append('event')
        df_predictive = pd.DataFrame(0, index=np.arange(len(df)), columns=cols)
        # for i in range(len(df)):
        #    data = [0] * len(df_predictive.columns)
        #    df_predictive.loc[i] = data
        for j, reg in df_regimes.iterrows():
            r = list(reg)
            r = [int(x) for x in r if (str(x) != "nan")]
            for k in r:
                df_predictive[df_predictive.columns[j]][k] = 1
        for i, row in events.iterrows():
            m = row["main indicator"]
            df_predictive['event'][m] = 1
        print(round(time.time() - start, 2), "sec. for successful data preparation")
        # TODO!:This is an optimization problem. Another agent should try all and find the best model#
        X, y = df_predictive.iloc[:, :-1].values.astype('int'), df_predictive.iloc[:, -1].values.astype('int')
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=0)

        try:
            # xgb = XGBClassifier(max_depth=10, n_jobs=-1, n_estimators=100,
            #                     scale_pos_weight=(len(y_train) - sum(y_train)) / sum(y_train))  # number of 0s/1s
            xgb = XGBClassifier(predictor="gpu_predictor", max_depth=10, n_jobs=-1, n_estimators=100,
                                scale_pos_weight=100).fit(X_train, y_train)
        except:
            print("GPU not detected. Using CPU.")
            xgb = XGBClassifier(max_depth=10, n_jobs=-1, n_estimators=100,
                                scale_pos_weight=(len(y_train) - sum(y_train)) / sum(y_train)).fit(X_train,
                                                                                                   y_train)  # number of 0s/1s

        y_pred = xgb.predict(X_test)
        y_test_labeled = ['event' if i == 1 else 'no_event' for i in y_test]
        y_pred_labeled = ['event' if i == 1 else 'no_event' for i in y_pred]
        m = confusion_matrix(y_test_labeled, y_pred_labeled, labels=['event', 'no_event'])
        print("Confusion matrix")
        print(m)
        tp = m[0][0]
        fp = m[1][0]
        tn = m[1][1]
        fn = m[0][1]
        s = precision_recall_fscore_support(y_test_labeled, y_pred_labeled, labels=['event'], zero_division=0)
        print("TP:", tp, "FP:", fp, 'TN:', tn, 'FN:', fn)
        print("Based on events, Precision:", s[0][0], "Recall:", s[1][0], "F1:", s[2][0])
        df_event_contributor = pd.DataFrame(columns=['contribution', 'indicator', 'event'])
        df_no_event_contributor = pd.DataFrame(columns=['contribution', 'indicator', 'event'])
        if tp > 0 or tn > 0:
            print("Calculating predictive power of indicators based on TP and TN...")
            feature_importances = xgb.feature_importances_
            event_no = 1
            not_event = 'no_event'  # weighted average of all true negatives to be taken
            for i in range(len(y_pred)):
                if (y_pred[i] + y_test[i] == 2) or (y_pred[i] + y_test[i] == 0):  # True positive
                    products = [a * b for a, b in zip(X_test[i], feature_importances)]
                    for j in range(len(products)):
                        p = products[j]
                        if p > 0:
                            li_name = df_predictive.columns[j]
                            if y_pred[i] + y_test[i] == 2:  # TP
                                df_event_contributor.loc[len(df_event_contributor)] = [p, li_name, event_no]
                            else:  # TN
                                df_no_event_contributor.loc[len(df_no_event_contributor)] = [p, li_name, not_event]
                    if y_pred[i] + y_test[i] == 2:
                        event_no = event_no + 1
        if len(df_no_event_contributor) > 0:
            df_no_event_contributor = df_no_event_contributor.groupby('indicator', as_index=False).mean()
            df_event_contributor = pd.concat([df_event_contributor, df_no_event_contributor], ignore_index=True)
            df_event_contributor = df_event_contributor.fillna(value="no_event")
        return df_event_contributor

    # def getBestPredictiveModel(self, events, df, all_regimes):
    #     """This function tests multiple models to come with the best predictive power.
    #     TODO: This is an optimization algorithm to be done by another agent. ANN models fail significantly.
    #     KNN Regressor works great but lacks predictive power. 2nd best is RandomForestClassifier"""
    #
    #     # train a model
    #     df_regimes = pd.DataFrame(all_regimes)
    #     # Predictive power
    #     print("Preparing the dataset for training")
    #     start = time.time()
    #     cols = list(df.columns)
    #     cols.append('event')
    #     df_predictive = pd.DataFrame(columns=cols)
    #     for i in range(len(df)):
    #         data = [0] * len(df_predictive.columns)
    #         df_predictive.loc[i] = data
    #     for j, reg in df_regimes.iterrows():
    #         r = list(reg)
    #         r = [int(x) for x in r if (str(x) != "nan")]
    #         for k in r:
    #             df_predictive[df_predictive.columns[j]][k] = 1
    #     for i, row in events.iterrows():
    #         m = row["main indicator"]
    #         df_predictive['event'][m] = 1
    #     print(round(time.time() - start, 2), "sec. for successful data preparation")
    #     # TODO!:This is an optimization problem. Another agent should try all and find the best model#
    #     X, y = df_predictive.iloc[:, :-1].values.astype('int'), df_predictive.iloc[:, -1].values.astype('int')
    #     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=0)
    #     print("Running RandomForestClassifier...")
    #     clf = RandomForestClassifier(max_depth=200, random_state=0, n_jobs=-1)
    #     clf.fit(X_train, y_train)
    #     y_pred = clf.predict(X_test)
    #
    #     y_test_labeled = ['event' if i == 1 else 'no_event' for i in y_test]
    #     y_pred_labeled = ['event' if i == 1 else 'no_event' for i in y_pred]
    #     m = confusion_matrix(y_test_labeled, y_pred_labeled, labels=['event', 'no_event'])
    #     tp = m[0][0]
    #     if tp == 0:
    #         print("Model could not predict events. Trying XGBoost")
    #         from xgboost import XGBClassifier
    #         try:
    #             xgb = XGBClassifier(n_jobs=-1)
    #             # xgb = XGBClassifier(predictor="gpu_predictor", n_jobs=-1)
    #         except Exception as e:
    #             print("GPU not detected. Using CPU.")
    #             xgb = XGBClassifier(n_jobs=-1)
    #         xgb = xgb.fit(X_train, y_train)
    #         y_pred = xgb.predict(X_test)
    #         y_test_labeled = ['event' if i == 1 else 'no_event' for i in y_test]
    #         y_pred_labeled = ['event' if i == 1 else 'no_event' for i in y_pred]
    #         m = confusion_matrix(y_test_labeled, y_pred_labeled, labels=['event', 'no_event'])
    #
    #     print("Confusion matrix")
    #     print(m)
    #     tp = m[0][0]
    #     fp = m[1][0]
    #     tn = m[1][1]
    #     fn = m[0][1]
    #     s = precision_recall_fscore_support(y_test_labeled, y_pred_labeled, labels=['event'], zero_division=0)
    #     print("TP:", tp, "FP:", fp, 'TN:', tn, 'FN:', fn)
    #     print("Based on events, Precision:", s[0][0], "Recall:", s[1][0], "F1:", s[2][0])
    #     print("Calculating predictive power of time series...")
    #     prediction, bias, contributions = ti.predict(clf, X_test)
    #     # we guessed all the 1's
    #     tmp_contrib = []
    #     for i in range(len(prediction)):
    #         if prediction[i][1] > prediction[i][0]:
    #             # print("Instance", i)
    #             # print("Bias (trainset mean)", bias[i])
    #             tmp_contrib.append(contributions[i])
    #
    #     df_event_contributor = pd.DataFrame(columns=['contribution', 'li name', 'event'])
    #     event = 1
    #     for c in tmp_contrib:
    #         for i in range(len(c)):
    #             if c[i][1] != 0:
    #                 contribution = abs(c[i][1])
    #                 li_name = df_predictive.columns[i]
    #                 df_event_contributor.loc[len(df_event_contributor)] = [contribution, li_name, event]
    #         event = event + 1
    #
    #     df_event_contributor = df_event_contributor.sort_values(['event', 'contribution'], ascending=[True, False])
    #     df_event_contributor.groupby('event').count()
    #     return df_event_contributor

    # def generateCorrelations(self, df_plotly, isDisplay=True, title='Correlations'):
    #     pio.renderers.default = 'browser'
    #
    #     def df_to_ploty(df):
    #         return {'z': df.values.tolist(),
    #                 'x': df.columns.tolist(),
    #                 'y': df.index.tolist()}
    #
    #     fig = go.Figure(data=go.Heatmap(df_to_ploty(df_plotly.corr())))
    #     fig.update_layout(title_text=title, title_x=0.5, title_y=0)
    #     fig.update_xaxes(side='top')
    #     fig.update_yaxes(autorange='reversed')
    #     if isDisplay: fig.show()
    #     title = title + "_" + re.sub(r'\W+', '_', str(datetime.datetime.now()))
    #     plotly.offline.plot(fig, filename=title + '.html', auto_open=False)

    def getRegimesFromChow(self, df, model='l1', chow_penalty=10):
        print("Running Cythonized Break Point Analysis")
        strucBreaks = []
        for i in range(len(df.columns)):
            signal = df.iloc[:, i].values
            my_bkps = run_cython.OptimizedPelt(model=run_cython.OptimizedNormalCost()).fit(np.array(signal)).predict(
                chow_penalty)
            strucBreaks.append(my_bkps)

        strucBreaks = timeSeriesL1Analytics.removeFPBreaks(df, strucBreaks, model)
        return strucBreaks

    def getIndicatorsFromIncreaseDecrease(self, df_events, df, window, percent_change_indicator_ratio,
                                          category="increase"):
        li = []
        mi = []
        ti = []
        for i, r in df_events.iterrows():
            l = int(r["leading indicator"])
            m = int(r["main indicator"])
            t = int(r["trailing indicator"])
            tmp_l = []
            tmp_m = []
            tmp_t = []
            if (l >= window - 1 and l < len(df) - 1):
                df_row = pd.DataFrame(df.iloc[l, :])
                if (category == 'increase'):
                    df_row = df_row[df_row >= percent_change_indicator_ratio].dropna()
                    if (len(df_row) < 1):
                        df_row = pd.DataFrame(df.iloc[l, :]).sort_values(by=[l], ascending=False).head(5)
                else:
                    df_row = df_row[df_row <= -percent_change_indicator_ratio].dropna()
                    if (len(df_row) < 1):
                        df_row = pd.DataFrame(df.iloc[l, :]).sort_values(by=[l], ascending=True).head(5)
                tmp_l = df_row.index.tolist()

            if (m >= window - 1 and m < len(df) - 1):
                df_row = pd.DataFrame(df.iloc[m, :])
                if (category == 'increase'):
                    df_row = df_row[df_row >= percent_change_indicator_ratio].dropna()
                    if (len(df_row) < 1):
                        df_row = pd.DataFrame(df.iloc[m, :]).sort_values(by=[m], ascending=False).head(5)
                else:
                    df_row = df_row[df_row <= -percent_change_indicator_ratio].dropna()
                    if (len(df_row) < 1):
                        df_row = pd.DataFrame(df.iloc[m, :]).sort_values(by=[m], ascending=True).head(5)
                tmp_m = df_row.index.tolist()

            if (t >= window - 1 and t < len(df) - 1):
                df_row = pd.DataFrame(df.iloc[t, :])
                if (category == 'increase'):
                    df_row = df_row[df_row >= percent_change_indicator_ratio].dropna()
                    if (len(df_row) < 1):
                        df_row = pd.DataFrame(df.iloc[t, :]).sort_values(by=[t], ascending=False).head(5)
                else:
                    df_row = df_row[df_row <= -percent_change_indicator_ratio].dropna()
                    if (len(df_row) < 1):
                        df_row = pd.DataFrame(df.iloc[t, :]).sort_values(by=[t], ascending=True).head(5)
                tmp_t = df_row.index.tolist()

            li.append(tmp_l)
            mi.append(tmp_m)
            ti.append(tmp_t)

        indicators = pd.DataFrame({"leading indicator": li, "main indicator": mi, "trailing indicator": ti})
        return indicators

    def getIndicatorsEventsPct(self, df, window, percent_change_event_ratio, percent_change_indicator_ratio,
                               enablePlotting):
        column_names = ["leading indicator", "main indicator", "trailing indicator", "event type (percent change)"]
        df_tmp = pd.DataFrame(df.copy())
        df_tmp["increase"] = df_tmp.apply(lambda x: x[x > 0].sum(), axis=1)
        df_tmp["decrease"] = df_tmp.apply(lambda x: x[x < 0].sum(), axis=1)
        df_tmp["combined"] = df_tmp["increase"] + df_tmp["decrease"].abs()
        df_tmp["normalized_increase"] = (df_tmp["increase"] - df_tmp["increase"].min()) / (
                df_tmp["increase"].max() - df_tmp["increase"].min())
        df_tmp["normalized_decrease"] = (df_tmp["decrease"] - df_tmp["decrease"].min()) / (
                df_tmp["decrease"].max() - df_tmp["decrease"].min())
        df_tmp["normalized_combined"] = (df_tmp["combined"] - df_tmp["combined"].min()) / (
                df_tmp["combined"].max() - df_tmp["combined"].min())
        plots = {}
        plots['normalized_increase'] = ""
        plots['normalized_decrease'] = ""
        X = np.array(df_tmp["normalized_increase"])
        peaks, properties = find_peaks(X, prominence=(percent_change_event_ratio, 1))
        if enablePlotting:
            prominences = peak_prominences(X, peaks)[0]
            countour_heights = X[peaks] - prominences
            plt.figure(0)
            plt.plot(X)
            plt.title("Percent Change: Normalized Increase")
            plt.plot(peaks, X[peaks], 'x', color='red')
            plt.vlines(x=peaks, ymin=countour_heights, ymax=X[peaks], color='black')
            base64_events = self.get_current_plot_as_base64()
            plots['normalized_increase'] = base64_events

        peaks = peaks.astype(object)
        t = ["increase"] * len(peaks)
        dict_tmp = {"leading indicator": properties["left_bases"].astype(object), "main indicator": peaks,
                    "trailing indicator": properties["right_bases"].astype(object), "event type (percent change)": t}
        df_events_increase = pd.DataFrame(dict_tmp)
        # df_tmp=pd.DataFrame(df.iloc[:,:-6])
        indicators_increase = self.getIndicatorsFromIncreaseDecrease(df_events_increase, df, window,
                                                                     percent_change_indicator_ratio, "increase")

        X = np.array(df_tmp["normalized_decrease"])
        peaks, properties = find_peaks(X, prominence=(percent_change_event_ratio, 1))
        if enablePlotting:
            prominences = peak_prominences(X, peaks)[0]
            countour_heights = X[peaks] - prominences
            plt.figure(1)
            plt.plot(X)
            plt.title("Percent Change: Normalized Decrease")
            plt.plot(peaks, X[peaks], 'x', color='red')
            plt.vlines(x=peaks, ymin=countour_heights, ymax=X[peaks], color='black')
            base64_events = self.get_current_plot_as_base64()
            plots['normalized_decrease'] = base64_events
        peaks = peaks.astype(object)
        t = ["decrease"] * len(peaks)
        dict_tmp = {"leading indicator": properties["left_bases"].astype(object), "main indicator": peaks,
                    "trailing indicator": properties["right_bases"].astype(object), "event type (percent change)": t}
        df_events_decrease = pd.DataFrame(dict_tmp, columns=column_names)
        # df_tmp=pd.DataFrame(df.iloc[:,:-6])
        indicators_decrease = self.getIndicatorsFromIncreaseDecrease(df_events_decrease, df, window,
                                                                     percent_change_indicator_ratio, "decrease")

        events = pd.concat([df_events_increase, df_events_decrease], axis=0).reset_index(drop=True)
        indicators = pd.concat([indicators_increase, indicators_decrease], axis=0).reset_index(drop=True)
        df_regimes = pd.DataFrame(df)  # df has normalized aggregations now
        df_regimes = df_regimes.mask(df_regimes >= percent_change_indicator_ratio, 1)
        df_regimes = df_regimes.mask(df_regimes <= - percent_change_indicator_ratio, 1)
        df_regimes = df_regimes.mask(df_regimes < 1, 0)
        all_regimes = df_regimes.values.astype(int).tolist()
        for i in range(len(all_regimes)):
            all_regimes[i] = [i for i, x in enumerate(all_regimes[i]) if x == 1]
        return events, indicators, all_regimes, plots['normalized_increase'], plots['normalized_decrease']

    def get_current_plot_as_base64(self):
        fig = plt.gcf()

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())

        uri = 'data:image/png;base64,' + urllib.parse.quote(string)
        return uri

    def createDashBoards(self, events, indicators, df_event_contributor, ts_all):
        pass

    def regimes2timestamps(self, all_regimes, bucket_size_msec, ts_min):
        if len(all_regimes) < 1:
            return []
        i = 0
        for r in all_regimes:
            if type(r) == int:
                all_regimes[i] = ts_min + bucket_size_msec * r
            else:
                for j in range(len(r)):
                    all_regimes[i][j] = ts_min + bucket_size_msec * all_regimes[i][j]
            i = i + 1
        return all_regimes

    def indicators2datetime(self, dict_events, bucket_size_msec, ts_min, timeZone='US/Pacific'):
        tz = pytz.timezone(timeZone)
        for key, value in dict_events.items():
            for k, v in value.items():
                if v == 0:
                    value[k] = "Unknown"
                elif type(v) == str:
                    continue
                else:
                    try:
                        value[k] = str(
                        datetime.datetime.fromtimestamp(int((v * bucket_size_msec + ts_min) / 1000), tz=tz).strftime(
                            "%Y-%m-%d %H:%M:%S"))
                    except Exception as a:
                        print(a)
        return dict_events
