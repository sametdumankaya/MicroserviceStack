import os

import pytz
import redis
from news_utils import NewsUtils
from datetime import datetime, timedelta
from neo4j_client import Neo4jClient
import nltk

if __name__ == "__main__":
    nltk.download('stopwords')
    nltk.download('vader_lexicon')
    output_redis_port = int(os.getenv("output_redis_port", 6379))
    neo4j_api_client = Neo4jClient("http://localhost:8003")
    n_utils = NewsUtils(redis.Redis(host="localhost", port=output_redis_port, decode_responses=True), neo4j_api_client)
    x = datetime.now()
    tz = pytz.timezone('America/Los_Angeles')
    x = tz.localize(x)
    weekday = x.weekday()
    if (weekday == 5 or weekday == 6):  # saturday/sunday
        print("Today is Saturday or Sunday. No news job will run.")
        pass
    else:
        delta = 1
        if weekday == 0:  # monday
            delta = 3
        todays_start_date_for_news = (x - timedelta(days=delta)).strftime('%Y-%m-%dT13:30:01')
        todays_end_date_for_news = x.strftime('%Y-%m-%dT%H:%M:%S')
        print(f"News job started - {datetime.now()}")
        n_utils.createNeo4jJsonAndRedis(symbol="all",
                                        page_size=10,
                                        todays_start_date_for_news=todays_start_date_for_news,
                                        todays_end_date_for_news=todays_end_date_for_news,
                                        industries=[],
                                        category="")
        print(f"News job finished {datetime.now()}")
