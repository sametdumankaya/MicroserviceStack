from typing import List
from datetime import datetime, date, timedelta
import time
import redis
import argparse
import sys
import nltk
#nltk.download('english')
nltk.download('stopwords')
nltk.download('vader_lexicon')
def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--msig_host',
        type=str,
        default='localhost',
        help='redis host for news output'
    )
    parser.add_argument(
        '--msig_port',
        type=int,
        default=6380,
        help='redis port for news output'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='all',
        help='stock market symbols whose news to be analyzes'
    )
    parser.add_argument(
        '--L2fileName',
        type=str,
        default='finL2Extension.graphml',
        help='L2 file for symbols and company names'
    )
    parser.add_argument(
        '--url',
        type=str,
        default="https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/search/NewsSearchAPI",
        help='url for news analysis'
    )
    parser.add_argument(
        '--api_key',
        type=str,
        default="b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",
        help='api key for news'
    )
    parser.add_argument(
        '--api_host',
        type=str,
        default="contextualwebsearch-websearch-v1.p.rapidapi.com",
        help='api key for news'
    )
    parser.add_argument(
        '--analysis_period',
        type=int,
        default=86400,
        help='news analysis period in seconds. Default is 3.5 hours'
    )
    parser.add_argument(
        '--page_size',
        type=int,
        default=10,
        help='max number of news per company to be analyzed'
    )
    parser.add_argument(
        '--doItNow',
        default=False,
        help='News analysis is set to be done 5:00am every working day. Use doItNow flag to trigger the analysis now.',
        action='store_true',
        dest='doItNow'
    )
    return parser

def preprocess_doc(single_doc):
    from nltk.corpus import stopwords
    import re
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

def analyzeNewsUsingRapidAPI(q:str,symbol,todays_start_date_for_news,todays_end_date_for_news,page_size=10,api_key="b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",api_host="contextualwebsearch-websearch-v1.p.rapidapi.com",category='company financial'):
    from datetime import datetime, timedelta
    import pandas as pd
    import requests
    import json
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/search/NewsSearchAPI"
    querystring = {
            "pageSize": f"{page_size}",
            "q": symbol + " "+q + " "+category,
            "autoCorrect": "false",
            "pageNumber":"1",
            "safeSearch": "false",
            "autoCirrect":"false",
            "toPublishedDate": todays_end_date_for_news,
            "fromPublishedDate": todays_start_date_for_news,
            "withThumbnails": "true"
    }

    headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': api_host,
            'useQueryString':'true'
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    response_json = json.loads(response.text)
    df_result=pd.DataFrame()
    if 'value' not in response_json:
        return df_result
    if(len(response_json['value'])==1 and "wikipedia" in response_json['value'][0]["url"]):
        return df_result
    sia = SentimentIntensityAnalyzer()
    ticker_financial_status_data=[]
    if 'value' in response_json:
        for news in response_json['value']:
            if("wikipedia" in news["url"]): continue
            date_published = news['datePublished']
            title = news['title']
            news_data = title + ' ' + news['body']
            url = news['url']

            news_str = preprocess_doc(news_data)
            vader_score = sia.polarity_scores(news_str)
            ticker_financial_status_data.append({
                    "symbol": symbol,
                    "fullName":q,
                    "neg": vader_score["neg"],
                    "pos":vader_score["pos"],
                    "neu":vader_score["neu"],
                    "compound":vader_score["compound"],    
                    "newsLink": url,
                    "newsTitle":title,
                    "newsBody":news['body'],
                    "date_published":date_published
                })
    df_result=pd.DataFrame(ticker_financial_status_data)
    return df_result
    
def mainLoop(cli_options) -> None:
    print("Starting daily news analysis process")
    import networkx as nx
    import pickle
    import distutils
    import pandas as pd
    import time
    import redis
    redis_queue=redis.Redis(host=cli_options.msig_host,port=cli_options.msig_port)
    if(not redis_queue.ping()):
        print("Unable to ping redis at",cli_options.msig_host, cli_options.msig_port)
        return
    G=nx.read_graphml(cli_options.L2fileName)
    all_nodes=pd.DataFrame.from_dict(dict(G.nodes(data=True)),orient='index')
     #If it is Monday, start from 3 days ago
    if(date.today().weekday()==0):
        delta=3
    #Don't run on saturdays
    elif(date.today().weekday() ==5):
        return
    #Don't run on sundays
    elif(date.today().weekday() ==6):
        return
    else:
        delta=1
    todays_start_date_for_news = (datetime.today()-timedelta(days=delta)).strftime('%Y-%m-%dT13:30:01')
    todays_end_date_for_news = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
    
    industries=list(all_nodes["industry"].dropna().unique())
    df_industry_news=pd.DataFrame()
    
    start=time.time()
    print("Analyzing industry news...")
    for ind in industries:
        df_tmp=analyzeNewsUsingRapidAPI(ind,"Economy",todays_start_date_for_news,todays_end_date_for_news,cli_options.page_size,cli_options.api_key,cli_options.api_host,category="Industry Financial")
        if(len(df_tmp)>0):
            df_industry_news=df_industry_news.append(df_tmp,ignore_index=True)
    #df_delete=pd.DataFrame(df_industry_news)
    df_industry_news.rename(columns={"symbol":"sector","fullName":"industry"},inplace=True)
    for i,r in df_industry_news.iterrows():
        tmp=all_nodes.loc[all_nodes["industry"]==r["industry"]].iloc[0,:]["sector"]
        df_industry_news.at[i,"sector"]=tmp
    dict_news={"category":"industry","date":todays_end_date_for_news,"data":df_industry_news}
    _=redis_queue.lpush("NewsIndustry",pickle.dumps(dict_news))
    print("Done in seconds=",time.time()-start)
    
    print("Analyzing companies=", cli_options.symbol)
    companies=pd.DataFrame(all_nodes[["symbol","fullName"]])
    if(cli_options.symbol=='all'):
        companies=companies.dropna()
    else:
        tmp_comp=cli_options.symbol.split(',')
        companies=companies.loc[companies['symbol'].isin(tmp_comp)]
    df_company_news=pd.DataFrame()
    for i,r in companies.iterrows():
        q=r["fullName"].strip()
        df_tmp=analyzeNewsUsingRapidAPI(q,r["symbol"].strip(),todays_start_date_for_news,todays_end_date_for_news,cli_options.page_size,cli_options.api_key,cli_options.api_host)
        if(len(df_tmp)>0):
           df_company_news=df_company_news.append(df_tmp,ignore_index=True) 
    dict_news={"category":"company","date":todays_end_date_for_news,"data":df_company_news}
    _=redis_queue.lpush("NewsCompany",pickle.dumps(dict_news))
    print("Sending news analysis results as 'Financial Status' to the front end...")
    sendFinancialStatus(df_company_news,df_industry_news)
    print("Done in seconds=",time.time()-start)

def sendFinancialStatus(df_company_news,df_industry_news,url='http://localhost:5000/FinancialStatus/PostFinancialStatus'):
    import json
    import requests
    import pandas as pd
    headers = {'accept': 'application/json'}
    htmlData=[]
    for i,row in df_company_news.iterrows():
        htmlData.append({"name":row["symbol"] + " - " + row["fullName"],"type":"Symbol","statusValue":row["compound"],"newsLink":row["newsLink"]})
    for j,row in df_industry_news.iterrows():
        htmlData.append({"name":row["sector"] + " - " + row["industry"],"type":"Industry","statusValue":row["compound"],"newsLink":row["newsLink"]})
        
    response = requests.post(url,headers=headers,json=htmlData)
    if(response.text):
        print(response.text)
    
def main(args: List[str]) -> None:
    from datetime import datetime, timedelta
    import time
    parser = get_cli_parser()
    cli_options = parser.parse_args(args)
    if(cli_options.doItNow):
       mainLoop(cli_options) 
       cli_options.doItNow = False
    while(True):
        x=datetime.today()
        day=x.day
        hour=x.hour
        minute=x.minute
        weekday=x.weekday()
        if(weekday==5):#saturday
           future=datetime(x.year, x.month, x.day,5,15)+timedelta(days=2)
           print("sleeping until ",future)
           time.sleep((future-x).total_seconds())
           mainLoop(cli_options) 
        elif(weekday==6):#sunday
           future=datetime(x.year, x.month, x.day,5,15)+timedelta(days=1)
           print("sleeping until ",future)
           time.sleep((future-x).total_seconds())
           mainLoop(cli_options) 
        else:
            if(hour==5 and minute>=14 and minute<=15):
                mainLoop(cli_options)
            elif(hour<5):
                future=datetime(x.year, x.month, x.day,5,15)
                print("sleeping until ",future)
                time.sleep((future-x).total_seconds())
                mainLoop(cli_options)
            else:
                if(weekday==4):
                    future=datetime(x.year, x.month, x.day,5,15)+timedelta(days=3)
                else:
                    future=datetime(x.year, x.month, x.day,5,15)+timedelta(days=1)
                print("sleeping until ",future)
                time.sleep((future-x).total_seconds())
                mainLoop(cli_options)
if __name__ == "__main__":
    main(sys.argv[1:])
