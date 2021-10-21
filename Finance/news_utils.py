import datetime
import pickle
import time
from datetime import datetime, timedelta

import networkx as nx
import nltk
import numpy as np
import pytz
import redis
import pandas as pd
import requests
import json
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from flair.models import TextClassifier
from flair.data import Sentence
from textblob import TextBlob
from nltk.corpus import stopwords
import re


class NewsUtils:
    def __init__(self, redis_output_client, neo4j_api_client):
        self.redis_output_client = redis_output_client
        self.neo4j_api_client = neo4j_api_client
        self.classifier = TextClassifier.load('en-sentiment')
        self.sia = SentimentIntensityAnalyzer()

    def preprocess_doc(self, single_doc):

        WPT = nltk.WordPunctTokenizer()
        stop_word_list = stopwords.words('english')
        number_pattern = re.compile('\d+')
        punc_pattern = re.compile('[\W_]+')
        # remove numbers
        single_doc = number_pattern.sub('', single_doc)
        # remove trailing spaces
        single_doc = single_doc.strip()
        # remove multiple spaces
        single_doc = single_doc.replace('\s+', ' ')
        # remove stop words
        tokens = WPT.tokenize(single_doc)
        filtered_tokens = [token for token in tokens if token not in stop_word_list]
        single_doc = ' '.join(filtered_tokens)
        return single_doc

    def analyzeNewsUsingRapidAPI(self, q: str, symbol, todays_start_date_for_news, todays_end_date_for_news, indOrSym,
                                 page_size=10,
                                 api_key="b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",
                                 api_host="contextualwebsearch-websearch-v1.p.rapidapi.com",
                                 category='company financial'):

        url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/search/NewsSearchAPI"
        querystring = {
            "pageSize": f"{page_size}",
            "q": symbol + " " + q + " " + category,
            "autoCorrect": "false",
            "pageNumber": "1",
            "safeSearch": "false",
            "autoCirrect": "false",
            "toPublishedDate": todays_end_date_for_news,
            "fromPublishedDate": todays_start_date_for_news,
            "withThumbnails": "true"
        }

        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': api_host,
            'useQueryString': 'true'
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        response_json = json.loads(response.text)
        df_result = pd.DataFrame()
        if 'value' not in response_json:
            return df_result
        if (len(response_json['value']) == 1 and "wikipedia" in response_json['value'][0]["url"]):
            return df_result

        ticker_financial_status_data = []

        if 'value' in response_json:
            for news in response_json['value']:
                if ("wikipedia" in news["url"]): continue
                date_published = news['datePublished']
                title = news['title']
                news_data = title + ' ' + news['body']
                url = news['url']
                body = news['body']

                news_str = self.preprocess_doc(news_data)
                vader_score = self.sia.polarity_scores(news_str)

                sentence = Sentence(news_str)
                self.classifier.predict(sentence)

                testimonial = TextBlob(news_str)

                ticker_financial_status_data.append({
                    "symbol": symbol,
                    "fullName": q,
                    "neg": vader_score["neg"],
                    "pos": vader_score["pos"],
                    "neu": vader_score["neu"],
                    "flair_value": sentence.labels[0].value,
                    "flair_score": sentence.labels[0].score,
                    "textblob_polarity": testimonial.sentiment.polarity,
                    "textblob_subjectivity": testimonial.sentiment.subjectivity,
                    "compound": vader_score["compound"],
                    "body": body,
                    "newsLink": url,
                    "newsTitle": title,
                    "date_published": date_published,
                    "indOrSym": indOrSym
                })
            df_result = pd.DataFrame(ticker_financial_status_data)
            self.pushNewsToRedis(df_result)

        return df_result

    def sendFinancialStatus(df_company_news, df_industry_news,
                            url='http://localhost:5000/FinancialStatus/PostFinancialStatus') -> object:
        headers = {'accept': 'application/json'}
        htmlData = []
        for i, row in df_company_news.iterrows():
            htmlData.append(
                {"name": row["symbol"] + " - " + row["fullName"], "type": "Symbol", "statusValue": row["compound"],
                 "newsLink": row["newsLink"]})
        for j, row in df_industry_news.iterrows():
            htmlData.append(
                {"name": row["sector"] + " - " + row["industry"], "type": "Industry", "statusValue": row["compound"],
                 "newsLink": row["newsLink"]})

        response = requests.post(url, headers=headers, json=htmlData)
        if (response.text):
            print(response.text)

    def analyzeNewsWithAPI(self, symbol, todays_start_date_for_news, todays_end_date_for_news, page_size=10,
                           category='company financial', industries=[]):
        print("Starting daily news analysis process")
        import networkx as nx
        import pickle
        import pandas as pd
        import time
        import redis

        redis_queue = redis.Redis(host='localhost', port=6379)
        if (not redis_queue.ping()):
            print("Unable to ping redis at", 'localhost', 6379)
            return
        G = nx.read_graphml('finL2Extension.graphml')
        all_nodes = pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index')
        delta = 1
        if (todays_start_date_for_news is np.nan):
            todays_start_date_for_news = (datetime.today() - timedelta(days=delta)).strftime('%Y-%m-%dT13:30:01')
        if (todays_end_date_for_news is np.nan):
            todays_end_date_for_news = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')

        if len(industries) > 0:
            industries = industries
        else:
            industries = list(all_nodes["industry"].dropna().unique())
        df_industry_news = pd.DataFrame()

        start = time.time()
        print("Analyzing industry news...")
        indOrSym = "ind"
        for ind in industries:
            df_tmp = self.analyzeNewsUsingRapidAPI(ind, "Economy", todays_start_date_for_news, todays_end_date_for_news,
                                                   indOrSym,
                                                   page_size, "b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",
                                                   "contextualwebsearch-websearch-v1.p.rapidapi.com",
                                                   category='Industry Financial')
            if (len(df_tmp) > 0):
                df_industry_news = df_industry_news.append(df_tmp, ignore_index=True)

        df_delete = pd.DataFrame(df_industry_news)
        df_industry_news.rename(columns={"symbol": "sector", "fullName": "industry"}, inplace=True)
        for i, r in df_industry_news.iterrows():
            tmp = all_nodes.loc[all_nodes["industry"] == r["industry"]].iloc[0, :]["sector"]
            df_industry_news.at[i, "sector"] = tmp
        dict_news = {"category": "industry", "date": todays_end_date_for_news, "data": df_industry_news}
        _ = redis_queue.lpush("NewsIndustry", pickle.dumps(dict_news))
        print("Done in seconds=", time.time() - start)

        print("Analyzing companies=", symbol)

        companies = pd.DataFrame(all_nodes[["symbol", "fullName"]])
        if (symbol == 'all'):
            companies = companies.dropna()
        else:
            tmp_comp = symbol.split(',')
            companies = companies.loc[companies['symbol'].isin(tmp_comp)]
        df_company_news = pd.DataFrame()
        count = 0
        indOrSym = "sym"
        for i, r in companies.iterrows():
            count = count + 1
            q = r["fullName"].strip()
            df_tmp = self.analyzeNewsUsingRapidAPI(q, r["symbol"].strip(), todays_start_date_for_news, indOrSym,
                                                   todays_end_date_for_news,
                                                   page_size, "b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",
                                                   "contextualwebsearch-websearch-v1.p.rapidapi.com")
            if (len(df_tmp) > 0):
                df_company_news = df_company_news.append(df_tmp, ignore_index=True)

        dict_news = {"category": "company", "date": todays_end_date_for_news, "data": df_company_news}
        _ = redis_queue.lpush("NewsCompany", pickle.dumps(dict_news))

        print("Done in seconds=", time.time() - start)

    def createNeo4jJsonAndRedis(self, symbol, todays_start_date_for_news, todays_end_date_for_news, page_size=10,
                                category='company financial', industries=[]):
        print("Starting daily news analysis process")
        redis_queue = redis.Redis(host='localhost', port=6379)
        if (not redis_queue.ping()):
            print("Unable to ping redis at", 'localhost', 6379)
            return
        G = nx.read_graphml('finL2Extension.graphml')
        all_nodes = pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index')
        delta = 1
        if (todays_start_date_for_news is np.nan):
            todays_start_date_for_news = (datetime.today() - timedelta(days=delta)).strftime('%Y-%m-%dT13:30:01')
        if (todays_end_date_for_news is np.nan):
            todays_end_date_for_news = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')

        if len(industries) > 0:
            industries = industries
        else:
            industries = list(all_nodes["industry"].dropna().unique())
        df_industry_news = pd.DataFrame()

        start = time.time()
        print("Analyzing industry news...")

        neo4jJson = {
            "nodes": [],
            "relation_triplets": []
        }
        node_index = 0
        neo4jJson["nodes"].append({
            "name": "News",
            "level": "L2.3",
            "index": node_index,
            "properties": {}

        })
        news_index = node_index
        node_index = node_index + 1
        indOrSym = "ind"
        count = 0
        for ind in industries:
            existing_SymbolorInd = next((node for node in neo4jJson["nodes"] if node["name"] == ind),
                                        None)
            if existing_SymbolorInd is None:
                neo4jJson["nodes"].append({
                    "name": ind,
                    "level": "L2.1",
                    "index": node_index,
                    "properties": {}
                })
                existing_SymbolorInd = node_index
                node_index = node_index + 1
            df_tmp = self.analyzeNewsUsingRapidAPI(ind, "Economy", todays_start_date_for_news,
                                                   todays_end_date_for_news, indOrSym,
                                                   page_size, "b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",
                                                   "contextualwebsearch-websearch-v1.p.rapidapi.com",
                                                   category='Industry Financial')

            start = time.time()
            print("Analyzing industry news...")
            indOrSym = "ind"
            # count = count +1
            # if count>5:
            #     break
            if (len(df_tmp) > 0):
                df_industry_news = df_industry_news.append(df_tmp, ignore_index=True)

        df_industry_news.rename(columns={"symbol": "sector", "fullName": "industry"}, inplace=True)
        for i, r in df_industry_news.iterrows():
            if type(r["industry"]) == str:
                tmp = all_nodes.loc[all_nodes["industry"] == r["industry"]].iloc[0, :]["sector"]
            else:
                tmp = all_nodes.loc[all_nodes["industry"] == r["industry"].sort_index(inplace=True)].iloc[0, :][
                    "sector"]
            df_industry_news.at[i, "sector"] = tmp
        dict_news = {"category": "industry", "date": todays_end_date_for_news, "data": df_industry_news}
        _ = redis_queue.lpush("NewsIndustry", pickle.dumps(dict_news))

        print("Done in seconds=", time.time() - start)

        relation_name = "intension"
        if df_tmp.size > 0:
            arr = df_tmp["newsTitle"]
            for idx, ind_news in arr.items():
                existing_news = next((node for node in neo4jJson["nodes"] if node["name"] == ind_news),
                                     None)
                if existing_news is None:
                    neo4jJson["nodes"].append({
                        "name": ind_news,
                        "level": "L1",
                        "index": node_index,
                        "properties": {'newsLink': df_tmp["newsLink"][idx], 'symbol': df_tmp["symbol"][idx],
                                       'neg': df_tmp["neg"][idx], 'pos': df_tmp["pos"][idx],
                                       'neu': df_tmp["neu"][idx], 'flair_value': df_tmp["flair_value"][idx],
                                       'flair_score': df_tmp["flair_score"][idx],
                                       'textblob_polarity': df_tmp["textblob_polarity"][idx],
                                       'textblob_subjectivity': df_tmp["textblob_subjectivity"][idx],
                                       'compound': df_tmp["compound"][idx],
                                       'body': df_tmp["body"][idx],
                                       'date_published': df_tmp["date_published"][idx]}

                    })
                    existing_news_index = node_index
                    node_index += 1
                else:
                    existing_news_index = existing_news["index"]
                neo4jJson["relation_triplets"].append(
                    [existing_news_index, relation_name, existing_SymbolorInd, {}])
                neo4jJson["relation_triplets"].append(
                    [existing_news_index, relation_name, news_index, {}])
            else:
                print('There is no news about :', ind)

        print("Done in seconds=", time.time() - start)

        print("Analyzing companies=", symbol)

        companies = pd.DataFrame(all_nodes[["symbol", "fullName"]])
        if (symbol == 'all'):
            companies = companies.dropna()
        else:
            tmp_comp = symbol.split(',')
            companies = companies.loc[companies['symbol'].isin(tmp_comp)]
        df_company_news = pd.DataFrame()
        indOrSym = "sym"
        for i, r in companies.iterrows():
            symbol = r["symbol"].strip()
            q = r["fullName"].strip()
            existing_SymbolorInd = next((node for node in neo4jJson["nodes"] if node["name"] == symbol),
                                        None)
            if existing_SymbolorInd is None:
                neo4jJson["nodes"].append({
                    "name": symbol,
                    "level": "L2.1",
                    "index": node_index,
                    "properties": {}
                })
                existing_SymbolorInd = node_index
                node_index = node_index + 1

            df_tmp = self.analyzeNewsUsingRapidAPI(q, r["symbol"].strip(), todays_start_date_for_news,
                                                   todays_end_date_for_news, indOrSym,
                                                   page_size, "b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",
                                                   "contextualwebsearch-websearch-v1.p.rapidapi.com")

            relation_name = "intension"
            if df_tmp.size > 0:
                arr = df_tmp["newsTitle"]
                for idx, compny_news in arr.items():
                    existing_news = next((node for node in neo4jJson["nodes"] if node["name"] == compny_news),
                                         None)
                    if existing_news is None:
                        neo4jJson["nodes"].append({
                            "name": compny_news,
                            "level": "L1",
                            "index": node_index,
                            "properties": {'newsLink': df_tmp["newsLink"][idx], 'symbol': df_tmp["symbol"][idx],
                                           'neg': df_tmp["neg"][idx], 'pos': df_tmp["pos"][idx],
                                           'neu': df_tmp["neu"][idx], 'flair_value': df_tmp["flair_value"][idx],
                                           'flair_score': df_tmp["flair_score"][idx],
                                           'textblob_polarity': df_tmp["textblob_polarity"][idx],
                                           'textblob_subjectivity': df_tmp["textblob_subjectivity"][idx],
                                           'compound': df_tmp["compound"][idx],
                                           'body': df_tmp["body"][idx],
                                           'date_published': df_tmp["date_published"][idx]}

                        })
                        existing_news_index = node_index
                        node_index += 1
                    else:
                        existing_news_index = existing_news["index"]
                    neo4jJson["relation_triplets"].append(
                        [existing_news_index, relation_name, existing_SymbolorInd, {}])
                    neo4jJson["relation_triplets"].append(
                        [existing_news_index, relation_name, news_index, {}])
            else:
                print('There is no news about :', r["fullName"].strip())
            # Send Redis according to OZ
            if (len(df_tmp) > 0):
                df_company_news = df_company_news.append(df_tmp, ignore_index=True)

        dict_news = {"category": "company", "date": todays_end_date_for_news, "data": df_company_news}
        _ = redis_queue.lpush("NewsCompany", pickle.dumps(dict_news))
        # analysis parameters
        metadata_dict = {"symbol": "", "todays_start_date_for_news": "", "todays_end_date_for_news": "",
                         "page_size": "", "industries": []}
        metadata_dict["symbol"] = symbol
        metadata_dict["todays_start_date_for_news"] = todays_start_date_for_news
        metadata_dict["todays_end_date_for_news"] = todays_end_date_for_news
        metadata_dict["page_size"] = page_size
        metadata_dict["industries"] = industries

        self.createNeo4j(neo4jJson, metadata_dict)

        print("Done in seconds=", time.time() - start)

        print("Sending news analysis results as 'Financial Status' to the front end...")
        self.sendFinancialStatus(df_company_news, df_industry_news)
        print("Done in seconds=", time.time() - start)

    def sendFinancialStatus(self, df_company_news, df_industry_news,
                            url='http://localhost:5000/FinancialStatus/PostFinancialStatus'):
        import requests
        headers = {'accept': 'application/json'}
        htmlData = []
        for i, row in df_company_news.iterrows():
            htmlData.append(
                {"name": row["symbol"] + " - " + row["fullName"], "type": "Symbol", "statusValue": row["compound"],
                 "newsLink": row["newsLink"]})
        for j, row in df_industry_news.iterrows():
            htmlData.append(
                {"name": row["sector"] + " - " + row["industry"], "type": "Industry", "statusValue": row["compound"],
                 "newsLink": row["newsLink"]})

        response = requests.post(url, headers=headers, json=htmlData)
        if (response.text):
            print(response.text)

    def createNeo4j(self, create_neo4json_object, metadata_dict):

        self.news_node_id = self.neo4j_api_client.find_node_id("News", "L2.3")
        if self.news_node_id is None:
            self.news_node_id = self.neo4j_api_client.create_node("News", "L2.3")
            self.analyzed_node_id = self.neo4j_api_client.create_node("Analyzed_News", "L2.0")
            self.metadata_node_id = self.neo4j_api_client.create_node("Metadata_News", "L2.0")
            self.params_node_id = self.neo4j_api_client.create_node("Params", "L1", metadata_dict)

            self.neo4j_api_client.add_intension(self.analyzed_node_id, self.news_node_id)
            self.neo4j_api_client.add_antisymmetric_relation(self.analyzed_node_id, self.metadata_node_id, "has")
            self.neo4j_api_client.add_intension(self.params_node_id, self.metadata_node_id)
        else:
            self.news_node_id = self.neo4j_api_client.find_node_id("News", "L2.3")
            self.analyzed_node_id = self.neo4j_api_client.find_node_id("Analyzed_News", "L2.0")
            self.metadata_node_id = self.neo4j_api_client.find_node_id("Metadata_News", "L2.0")
            self.params_node_id = self.neo4j_api_client.find_node_id("Params", "L1")

        self.neo4j_api_client.create_news_graph(create_neo4json_object, "L2")

    def pushNewsToRedis(self, df_result):
        counter = 0
        queue_entry = {}

        for row in df_result.iterrows():
            key = "NewsSentimentResult"
            news_sentiment_result = "POSITIVE"
            sentiment_result = []
            sentiment_result_value = 0
            news_sentiment_result_vader = "POSITIVE"
            news_sentiment_result_textBlob = "POSITIVE"
            news_sentiment_result_flair = "POSITIVE"
            if row[1]["neg"] > row[1]["pos"]:
                news_sentiment_result_vader = "NEGATIVE"
                sentiment_result.append(news_sentiment_result_vader)
                sentiment_result_value = sentiment_result_value + row[1]["neg"]
            else:
                sentiment_result_value = sentiment_result_value + row[1]["pos"]
            news_sentiment_result_flair = row[1]["flair_value"]
            sentiment_result.append(news_sentiment_result_flair)
            if row[1]["textblob_polarity"] < 0:
                news_sentiment_result_textBlob = "NEGATIVE"
                sentiment_result.append(news_sentiment_result_textBlob)
                sentiment_result_value = sentiment_result_value - row[1]["textblob_polarity"]
            else:
                sentiment_result_value = sentiment_result_value + row[1]["textblob_polarity"]
            negCount = sentiment_result.count('NEGATIVE')
            if negCount > 1:
                news_sentiment_result = "NEGATIVE"

            queue_entry[row[1]["symbol"]] = json.dumps(
                {"symbol": row[1]["symbol"], "date_published": row[1]["date_published"],
                 "news_title": row[1]["newsTitle"], "newsLink": row[1]["newsLink"], "newsBody": row[1]["body"],
                 "news_sentiment_result": news_sentiment_result,
                 "news_sentiment_result_value": sentiment_result_value, "indOrSym": row[1]["indOrSym"]})
        if len(queue_entry) > 0:
            self.redis_output_client.xadd("NewsSentimentResult", queue_entry)

    def getNewsFromRedis(self, count, date):

        dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
        time = dt.strftime('%s')
        dailyNews = {}
        topNews = {}
        try:
            news = self.redis_output_client.xrange("NewsSentimentResult", f'{time}', "+")
            for item, idx in news:
                for key, value in idx.items():
                    newsValue = json.loads(value)
                    if newsValue["indOrSym"] == "sym":
                        if key in dailyNews:
                            dailyNews[key].append({"news_sentiment_result": newsValue["news_sentiment_result"],
                                                   "news_sentiment_result_value": newsValue[
                                                       "news_sentiment_result_value"]})
                        else:
                            dailyNews[key] = [{"news_sentiment_result": newsValue["news_sentiment_result"],
                                               "news_sentiment_result_value": newsValue["news_sentiment_result_value"]}]
        except:
            print("hata")

        for key, value in dailyNews.items():
            pos = 0
            neg = 0
            posCount = 0
            negCount = 0
            for val in value:
                if val["news_sentiment_result"] == "POSITIVE":
                    posCount = posCount + 1
                    pos = pos + val["news_sentiment_result_value"]
                else:
                    negCount = negCount + 1
                    neg = neg + val["news_sentiment_result_value"]
            if posCount > negCount:
                topNews[key] = {"label": "POSITIVE", "value": pos / posCount}
            elif posCount == negCount:
                if pos > neg:
                    topNews[key] = {"label": "POSITIVE", "value": pos / posCount}
                else:
                    topNews[key] = {"label": "NEGATIVE", "value": neg / negCount}
            else:
                topNews[key] = {"label": "NEGATIVE", "value": neg / negCount}

        positiveDict = {}
        negativeDict = {}
        for item in topNews.items():
            if item[1]["label"] == "NEGATIVE":
                negativeDict[item[0]] = item[1]
            else:
                positiveDict[item[0]] = item[1]
        sortedPosList = sorted(positiveDict, key=lambda x: (positiveDict[x]['value']), reverse=True)
        sortedNegList = sorted(negativeDict, key=lambda x: (negativeDict[x]['value']), reverse=True)

        sortedPosList = sortedPosList[:count]
        sortedNegList = sortedNegList[:count]
        returnDict = {"posNews": sortedPosList, "negNews": sortedNegList}
        return returnDict

    def getNewsFromRedisBetweenDates(self, startDate, endDate):
        tz = pytz.timezone('America/Los_Angeles')
        start_timestamp = int(
            tz.localize(datetime.strptime(startDate, "%Y-%m-%d %H:%M:%S")).timestamp()) * 1000
        end_timestamp = int(
            tz.localize(datetime.strptime(endDate, "%Y-%m-%d %H:%M:%S")).timestamp()) * 1000
        try:
            news = self.redis_output_client.xrange("NewsSentimentResult", f'{start_timestamp}', f'{end_timestamp}')

        except:
            print("error")

        returnDict = {"news": news}
        return returnDict
