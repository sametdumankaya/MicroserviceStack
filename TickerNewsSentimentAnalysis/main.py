import argparse
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
import re
import time

firm_size = 100

oldest_date_for_news = datetime(2018, 1, 1, 0, 0, 0).strftime('%Y-%m-%dT%H:%M:%S')
todays_start_date_for_news = datetime.today().strftime('%Y-%m-%dT00:00:00')
todays_end_date_for_news = datetime.today().strftime('%Y-%m-%dT23:59:59')

page_size = 50

WPT = nltk.WordPunctTokenizer()
stop_word_list = stopwords.words('english')

number_pattern = re.compile('\d+')
punc_pattern = re.compile('[\W_]+')


def preprocess_doc(single_doc):
    # remove numbers
    single_doc = number_pattern.sub('', single_doc)

    # remove punctuation and underscore
    # single_doc = punc_pattern.sub(' ', single_doc)

    # make lowercase
    # single_doc = single_doc.lower()

    # remove trailing spaces
    single_doc = single_doc.strip()

    # remove multiple spaces
    single_doc = single_doc.replace('\s+', ' ')

    # remove stop words
    tokens = WPT.tokenize(single_doc)
    filtered_tokens = [token for token in tokens if token not in stop_word_list]
    single_doc = ' '.join(filtered_tokens)
    return single_doc


nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

df = pd.read_csv("firms_joined_v2.csv", header=None)
all_unique_tickers = ",".join(df[0].unique())

parser = argparse.ArgumentParser(description='Sentiment analysis of the news about companies.')

parser.add_argument("--startDate", help="start date of the news", type=str, default=todays_start_date_for_news,
                    required=False)
parser.add_argument("--companies", help="comma seperated list of companies", type=str, default=all_unique_tickers,
                    required=False)

args = parser.parse_args()
input_start_date = args.startDate
input_companies = args.companies

ticker_financial_status_data = []
firm_list = input_companies.split(",")[0:firm_size]

total_news_count = 0
start_time_sentiment = time.time()
for ticker in firm_list:
    page_number = 1
    while True:
        url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/search/NewsSearchAPI"
        ticker_name = ticker.strip().upper()
        querystring = {
            "pageSize": f"{page_size}",
            "q": ticker_name,
            "autoCorrect": "false",
            "pageNumber": f"{page_number}",
            "safeSearch": "false",
            "toPublishedDate": todays_end_date_for_news,
            "fromPublishedDate": input_start_date,
            "withThumbnails": "false"
        }

        headers = {
            'x-rapidapi-key': "b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",
            'x-rapidapi-host': "contextualwebsearch-websearch-v1.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        response_json = json.loads(response.text)
        page_number += 1

        if not response_json['value']:
            break

        total_news_count += len(response_json['value'])
        for news in response_json['value']:
            news_id = news['id']
            date_published = news['datePublished']
            title = news['title']
            news_data = title + ' ' + news['body']
            url = news['url']

            news_str = preprocess_doc(news_data)
            vader_score = sia.polarity_scores(news_str)

            ticker_financial_status_data.append({
                "name": ticker_name,
                "type": "Symbol",
                "statusValue": vader_score["compound"],
                "newsLink": url
            })
end_time_sentiment = time.time()

start_time_post_status = time.time()
post_status_headers = {'accept': 'application/json'}
post_status_url = 'http://localhost:5000/FinancialStatus/PostFinancialStatus'
post_status_response = requests.post(post_status_url, headers=post_status_headers, json=ticker_financial_status_data)
print(f"Response Code: {post_status_response.status_code}")
end_time_post_status = time.time()

print(f"For {firm_size} firms:")
print(f"Sentiment analysis time: {end_time_sentiment - start_time_sentiment} seconds")
print(f"Post status time: {end_time_post_status - start_time_post_status} seconds")
print(f"In total {total_news_count} news analyzed.")
