import requests
from urllib.request import Request, urlopen
import urllib
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import networkx as nx
from selenium import webdriver

headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,*/*;q=0.8"}

def google(q):
    q = '+'.join(q.split())
    url = 'https://www.google.com/search?q=' + q + '&ie=utf-8&oe=utf-8'
    reqest = Request(url,headers=headers)
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    return soup.text

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

def getCompanyNameFromTicker(tickers):
    import regex as re
    from tqdm import tqdm
    G=nx.MultiDiGraph()
    res=google("what is ticker?").split("Search Results")[-1]
    res=re.findall("[A-Z].*?[\.!]", res, re.MULTILINE | re.DOTALL )
    for d in res:
        if(" is " in d or " are " in d or " was " in d or " were " in d or " been " in d ):
            description=d.split()
            description=[x for x in description if x.isalpha()]
            description=" ".join(description)
            break
    G.add_node("ticker", description=description)
    pbar=tqdm(total=len(tickers),position=0)
    for i in range(len(tickers)):
        t=tickers[i]
        G.add_edge(t,"ticker",relation="is")
        res=yahooFin(t)
        #TODO:
        #REMOVE LISTS FROM res
        G.add_node(res["fullName"].strip(), **res)
        G.add_edge(t, res["fullName"].strip(), relation="is")
        pbar.update(1)
        #G.remove_node(res["fullName"].strip())
    return G
if __name__ == "__main__":
    import pickle
    with open('all_data.pkl', 'rb') as f:
        tickers = pickle.load(f)       
    first_list = list(tickers["df_price_data"].columns)
    second_list =list(tickers["df_volume_data"].columns)
    tickers= list(set(first_list) | set(second_list))
    G=getCompanyNameFromTicker(tickers)
    nodes=list(G.nodes(data=True))
    for n in nodes:
        for ky,value in n[1].items():
            if(type(value)==list):
                n[1][ky]=','.join(map(str,value))
    nx.write_graphml_lxml(G,"finL2Extension.graphml")    
    # all_nodes=pd.DataFrame.from_dict(dict(G.nodes(data=True)),orient='index')
    # all_nodes.to_csv('companies_updated.csv',header=True,index=False)
    # #G=nx.read_graphml("finL2Extension.graphml")
    # for t in all_companies:
    #     subg=nx.ego_graph(G,t,1).nodes(data=True)
    #     for n in subg:
    #         if(len(n)>1):
    #             if('industry' in n[1].keys()):
    #                 G.nodes[n[0]]['symbol']=t
    # nodes=list(G.nodes(data=True))
    # for n in nodes:
    #     for ky,value in n[1].items():
    #         if(ky=='symbol'):
    #            if(n[1]['symbol']=='ZTR'):
    #               print(G.nodes[n[0]]["sector"])
    
    
    
    