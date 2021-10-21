#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 16:37:09 2020

@author: ozkan
"""
import MSig_Functions as MSig
import pandas as pd
import requests
from urllib.request import Request, urlopen
import urllib
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import networkx as nx
from selenium import webdriver
from datetime import datetime
from pytz import timezone
def yahooFin(q):
    from json import loads
    from bs4 import BeautifulSoup
    import os
    url="https://finance.yahoo.com/quote/" +q+"?p="+q
    browser = webdriver.PhantomJS(os.getcwd()+'/phantomjs/bin/phantomjs')
    browser.get(url)
    page = browser.page_source
    soup = BeautifulSoup(page,"html.parser",from_encoding="iso-8859-1")
    fullName=str(soup).split("<title>")[1].split("(")[0]
    summaryData={}
    if("summaryProfile" in str(soup)):
        try:
            data = str(soup).split('summaryProfile')[-1]
            data=data.split("recommendationTrend")[0]
            data=data[2:-2]
            if(len(data)>0):summaryData=loads(data)
        except Exception as e:
            pass
    summaryData.update({"fullName":fullName})
    return summaryData


from_time=0
to_time=-1
prefix="rts1:01:symbol:"
bucket_size_msec=60000
filters=["SYMSET=ACTIVE"]
aggregation_type="last"

output_redis_host=input_redis_host="localhost"
ports=[item for item in range(6400,6470)]
df_aggregate=pd.DataFrame(columns=["company", "port","start_ts","end_ts","start_date","end_date","sector","industry"])
tz=timezone('US/Pacific')
result=[]
for p in ports:
    input_redis_port=p
    all_data=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=input_redis_port,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    for i in range(len(all_data['df_price_data'].columns)):
        comp=all_data['df_price_data'].columns[i]
        port=p
        start_ts=all_data['ts_price_min']
        end_ts=all_data['ts_price_max']
        start_date=str(datetime.fromtimestamp(start_ts/1000,tz=tz))
        end_date=str(datetime.fromtimestamp(end_ts/1000,tz=tz))
        result.append({"p":p, "start_date":start_date, "end_date":end_date})
        break
        #result=yahooFin(comp)
        #sector=result["sector"]
        #industry=result["industry"]
        #df_aggregate.loc[len(df_aggregate)]=[comp,port,start_ts,end_ts,start_date,end_date,'','']
    
    df_dates=pd.DataFrame(result)   
    tmp_6401=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6401,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    tmp_6405=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6405,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    
    tmp_6402=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6402,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    tmp_6403=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6403,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    tmp_6404=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6404,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    
    tmp_6422=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6422,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    tmp_6423=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6423,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)

    tmp_6400=MSig.get_data_from_mrF(redis_host=input_redis_host,redis_port=6400,
                                 from_time=from_time,to_time=to_time,
                                 query_key=None,prefix=prefix,
                                 aggregation_type=aggregation_type,bucket_size_msec=bucket_size_msec,filters=filters)
    
    tmp_6401["df_price_data"].equals( tmp_6405["df_price_data"])
    tmp_6402["df_price_data"].equals( tmp_6403["df_price_data"])
    tmp_6402["df_price_data"].equals( tmp_6404["df_price_data"])
    tmp_6423["df_price_data"].equals( tmp_6422["df_price_data"])
    tmp_6400["df_price_data"].equals( tmp_6401["df_price_data"])
    
    all_companies=list(df_aggregate["company"].values)
    all_companies=list(set(all_companies))
    df_sector_industry=pd.DataFrame(columns=['company',"sector","industry"])
    for i in range(952,len(all_companies)):
        comp=all_companies[i]
        print(i, comp)
        try:
            result=yahooFin(comp)
            sector=result["sector"]
            industry=result["industry"]
            df_sector_industry.loc[len(df_sector_industry)]=[comp,sector,industry]
        except Exception as e:
            print(e)
            pass
    
    
  