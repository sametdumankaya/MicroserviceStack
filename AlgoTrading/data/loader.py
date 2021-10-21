import json
from abc import ABC, abstractmethod
import redis
from redistimeseries.client import Client
import pandas as pd
from datetime import datetime, timedelta
import random
import requests
import time


class DataLoader(ABC):
    @abstractmethod
    def get_latest_data(self, sample_rate_msec: int):
        pass

    @abstractmethod
    def get_news(self, start_date_time: str, end_date_time: str):
        pass


class LiveStreamingDataLoader(DataLoader):
    def get_news(self, start_date_time_msec: int, end_date_time_msec: int):
        # implement after HistoricalDatasource
        pass

    def __init__(self, input_redis_host: str, input_redis_port: int, price_label: str, volume_label: str,
                 bucket_size_msec: int):
        self.input_redis = redis.Redis(host=input_redis_host, port=input_redis_port, decode_responses=True)
        self.input_rts = Client(self.input_redis)
        self.price_filter = price_label
        self.volume_filter = volume_label
        self.bucket_size_msec = bucket_size_msec

    def get_latest_data(self, sample_rate_msec: int):
        now = datetime.now()
        redis_response = self.input_rts.mrange(int((now - timedelta(milliseconds=sample_rate_msec)).timestamp() * 1000),
                                               int(now.timestamp() * 1000),
                                               [f"SYMSET=({self.price_filter},{self.volume_filter})"],
                                               aggregation_type="last",
                                               bucket_size_msec=self.bucket_size_msec)

        df_list = []
        for item in redis_response:
            current_df = pd.DataFrame({
                "datetime": [x[0] for x in item[next(iter(item))][1]],
                next(iter(item)): [x[1] for x in item[next(iter(item))][1]]
            })

            current_df.set_index("datetime", inplace=True)
            df_list.append(current_df)

        stock_df = pd.concat(df_list, axis=1)
        stock_df.index = pd.to_datetime(stock_df.index, unit="ms")
        stock_df.fillna(method="ffill", inplace=True)
        stock_df.fillna(method="bfill", inplace=True)
        # if a symbol's price or volume data is full of NANs, drop it
        stock_df.dropna(axis="columns", inplace=True)
        stock_df.reset_index(inplace=True)
        return stock_df if stock_df.shape[0] > 0 else None


class RandomDataLoader(DataLoader):
    def get_news(self, start_date_time_msec: int, end_date_time_msec: int):
        pass

    def __init__(self, stock_count: int):
        self.stock_count = stock_count

    def get_latest_data(self, sample_rate_msec: int):
        now = datetime.now()
        data = []
        for i in range(int(sample_rate_msec / 1000)):
            record = {
                "datetime": int((now - timedelta(seconds=i)).timestamp() * 1000)
            }
            for stock_number in range(self.stock_count):
                record[f"stock_{stock_number}_price"] = random.randint(50, 100)
                record[f"stock_{stock_number}_volume"] = random.randint(500, 1000)
            data.insert(0, record)
        return pd.DataFrame(data)


class HistoricalDataLoader(DataLoader):
    def __init__(self, input_redis_host: str, input_redis_port: int, start_timestamp_msec: int, end_timestamp_msec: int,
                 price_label: str, volume_label: str, bucket_size_msec: int, news_host: str,
                 news_port: int):
        self.input_redis = redis.Redis(host=input_redis_host, port=input_redis_port, decode_responses=True)
        self.input_rts = Client(self.input_redis)
        self.current_start_timestamp_msec = start_timestamp_msec
        self.start_timestamp_msec = start_timestamp_msec
        self.end_timestamp_msec = end_timestamp_msec
        self.price_filter = price_label
        self.volume_filter = volume_label
        self.bucket_size_msec = bucket_size_msec
        self.news_host = news_host
        self.news_port = news_port

    def wait_for_availability(self):
        while True:
            try:
                self.input_redis.ping()
                return True
            except:
                continue

    def get_news(self, start_date_time: str, end_date_time: str):
        data = requests.post(f"http://{self.news_host}:{self.news_port}/getNewsFromRedisBetweenDates/",
                             json={
                                 "startDate": start_date_time,
                                 "endDate": end_date_time
                             }).json()

        if len(data["result"]["news"]) > 0:
            print(f"{len(data['result']['news'])} news found between {start_date_time} and {end_date_time}")
            items = []
            for item in data["result"]["news"]:
                key = next(iter(item[1]))
                items.append(json.loads(item[1][key]))
            df = pd.DataFrame(items)
            df.rename(columns={
                'news_sentiment_result_value': 'compound',
                'newsBody': "body",
                'news_title': "newsTitle"
            }, inplace=True)
            df_industry_news = df[df["indOrSym"] == "ind"]
            dict_industry = {
                "category": "industry",
                "date": start_date_time,
                "data": df_industry_news
            }
            df_company_news = df[df["indOrSym"] == "sym"]
            dict_company = {
                "category": "company",
                "date": start_date_time,
                "data": df_company_news
            }
        else:
            print(f"No data available between {start_date_time} and {end_date_time}")
            return None, None

        return dict_industry, dict_company

    def get_latest_data(self, sample_rate_msec: int):
        if self.current_start_timestamp_msec < self.end_timestamp_msec:
            redis_response = []
            while True:
                try:
                    redis_response = self.input_rts.mrange(self.current_start_timestamp_msec,
                                                           self.current_start_timestamp_msec + sample_rate_msec,
                                                           [f"SYMSET=({self.price_filter},{self.volume_filter})"],
                                                           aggregation_type="last",
                                                           bucket_size_msec=self.bucket_size_msec)
                    break
                except redis.exceptions.BusyLoadingError:
                    print("Redis backup file still being loaded. Waiting 5 seconds to try again.")
                    time.sleep(5)
                    continue

            df_list = []
            for item in redis_response:
                current_df = pd.DataFrame({
                    "datetime": [x[0] for x in item[next(iter(item))][1]],
                    next(iter(item)): [x[1] for x in item[next(iter(item))][1]]
                })

                current_df.set_index("datetime", inplace=True)
                df_list.append(current_df)

            stock_df = pd.concat(df_list, axis=1)
            stock_df.index = pd.to_datetime(stock_df.index, unit="ms")
            stock_df.fillna(method="ffill", inplace=True)
            stock_df.fillna(method="bfill", inplace=True)
            # if a symbol's price or volume data is full of NANs, drop it
            stock_df.dropna(axis="columns", inplace=True)
            stock_df.reset_index(inplace=True)
            self.current_start_timestamp_msec += sample_rate_msec
            return stock_df if stock_df.shape[0] > 0 else None
        else:
            return None
