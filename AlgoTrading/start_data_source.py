import datetime
import os
import time
import pytz

from data import loader, exporter


def query_and_push_trade_data(data_loader: loader.DataLoader, data_exporter: exporter.DataExporter,
                              sample_rate_millisec: int, wait_time_millisec: int):
    start_time = datetime.datetime.now()
    latest_data = data_loader.get_latest_data(sample_rate_millisec)
    redis_push_data = data_exporter.dataframe_to_key_timestamp_value_tuples(latest_data)
    data_exporter.push_stock_data_to_redis(redis_push_data)
    elapsed = datetime.datetime.now() - start_time
    print(f"Elapsed time: {elapsed.total_seconds()} seconds")
    print(f"{len(redis_push_data)} stock records pushed to output redis")
    if wait_time_millisec > 0:
        print(f"Waiting for {wait_time_millisec / 1000} seconds.\n")
        time.sleep(wait_time_millisec / 1000)


if __name__ == "__main__":
    # can be "live", "historical" or "random"
    stream_type = os.getenv("stream_type", "historical")
    sample_rate_msec = int(os.getenv("sample_rate_msec", 10 * 1000))
    wait_time_msec = int(os.getenv("wait_time_msec", 0))

    # news parameters
    news_port = int(os.getenv("news_port", 8007))
    if stream_type == "random":
        print("random")
        stock_count = int(os.getenv("stock_count", 5))
        output_redis_port = int(os.getenv("output_redis_port", 6379))
        redis_loader = loader.RandomDataLoader(stock_count)
        redis_exporter = exporter.DataExporter("localhost", output_redis_port)
        while True:
            query_and_push_trade_data(redis_loader, redis_exporter, sample_rate_msec, wait_time_msec)
    elif stream_type == "historical":
        print("historical")
        input_redis_port = int(os.getenv("input_redis_port", 6381))
        output_redis_port = int(os.getenv("output_redis_port", 6379))
        price_label = os.getenv("price_label", "ACTIVE_PRICE")
        volume_label = os.getenv("volume_label", "ACTIVE_VOLUME")
        bucket_size_msec = int(os.getenv("bucket_size_msec", 1000))
        date = os.getenv("date")

        tz = pytz.timezone('America/Los_Angeles')

        start_timestamp = int(
            tz.localize(datetime.datetime.strptime(date + " 06:29:59", "%Y-%m-%d %H:%M:%S")).timestamp()) * 1000
        end_timestamp = int(
            tz.localize(datetime.datetime.strptime(date + " 13:09:59", "%Y-%m-%d %H:%M:%S")).timestamp()) * 1000
        redis_loader = loader.HistoricalDataLoader("localhost", input_redis_port, start_timestamp, end_timestamp,
                                                   price_label, volume_label, bucket_size_msec, "localhost",
                                                   news_port)
        redis_exporter = exporter.DataExporter("localhost", output_redis_port)
        are_news_pushed = False
        while True:
            if redis_loader.current_start_timestamp_msec < redis_loader.end_timestamp_msec:
                print(
                    f"Getting data between "
                    f"{tz.localize(datetime.datetime.fromtimestamp(redis_loader.current_start_timestamp_msec / 1000))} and "
                    f"{tz.localize(datetime.datetime.fromtimestamp((redis_loader.current_start_timestamp_msec + sample_rate_msec) / 1000))}")

                if not are_news_pushed:
                    date_1 = str(datetime.datetime.strptime(date, "%Y-%m-%d"))
                    date_2 = str(datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(days=1))
                    dict_industry, dict_company = redis_loader.get_news(date_1, date_2)
                    redis_exporter.push_news_data_to_redis(dict_industry, dict_company)
                    are_news_pushed = True

                query_and_push_trade_data(redis_loader, redis_exporter, sample_rate_msec, wait_time_msec)
                print("OK\n")
            else:
                print("Datasource operation finished. Exiting.")
                break
    else:
        print("live")
        input_redis_port = int(os.getenv("input_redis_port", 6381))
        output_redis_port = int(os.getenv("output_redis_port", 6379))
        price_label = os.getenv("price_label", "ACTIVE_PRICE")
        volume_label = os.getenv("volume_label", "ACTIVE_VOLUME")
        bucket_size_msec = int(os.getenv("bucket_size_msec", 1000))
        redis_loader = loader.LiveStreamingDataLoader("localhost", input_redis_port, price_label, volume_label,
                                                      bucket_size_msec)
        redis_exporter = exporter.DataExporter("localhost", output_redis_port)
        while True:
            query_and_push_trade_data(redis_loader, redis_exporter, sample_rate_msec, wait_time_msec)
