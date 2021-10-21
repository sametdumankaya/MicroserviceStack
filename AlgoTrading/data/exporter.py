import redis
from redistimeseries.client import Client
import pandas as pd
import redis.exceptions
import pickle


class DataExporter:
    def __init__(self, output_redis_host: str, output_redis_port):
        self.output_redis = redis.Redis(host=output_redis_host, port=output_redis_port, decode_responses=True)
        self.output_rts = Client(self.output_redis)

    @staticmethod
    def get_unique_key_names(key_timestamp_value_tuples: list):
        uniques = []
        for ktv in key_timestamp_value_tuples:
            if ktv[0] not in uniques:
                uniques.append(ktv[0])
        return uniques

    def push_stock_data_to_redis(self, key_timestamp_value_tuples: list):
        unique_keys = DataExporter.get_unique_key_names(key_timestamp_value_tuples)
        for unique_key in unique_keys:
            try:
                self.output_rts.create(unique_key, labels={
                    "SYMSET": "ACTIVE_VOLUME" if "volume" in unique_key else "ACTIVE_PRICE"
                })
            except redis.exceptions.ResponseError:
                continue
        for i in range(0, len(key_timestamp_value_tuples), 1000):
            self.output_rts.madd(key_timestamp_value_tuples[i: i + 1000])

    def push_news_data_to_redis(self, dict_industry: dict, dict_company: dict):
        if dict_company is not None and dict_industry is not None:
            self.output_redis.lpush("NewsIndustry", pickle.dumps(dict_industry))
            self.output_redis.lpush("NewsCompany", pickle.dumps(dict_company))

    def dataframe_to_key_timestamp_value_tuples(self, df: pd.DataFrame):
        result = []
        if df is not None:
            for col in df.columns.tolist():
                if col != "datetime":
                    for _, row in df[["datetime", col]].iterrows():
                        result.append((col, int(row["datetime"].timestamp() * 1000), row[col]))
        return result
