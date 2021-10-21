import pandas as pd
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
import warnings
import re
warnings.simplefilter("ignore", DeprecationWarning)
from sklearn.decomposition import LatentDirichletAllocation as LDA
from sklearn.model_selection import GridSearchCV
sns.set_style('whitegrid')
import networkx as nx
TAG_RE = re.compile(r'<[^>]+>')

def plot_N_most_common_words(seriesColumn :pd.Series,N:int, ignore_word_list:list)->None:
    """This function draws a bar graph from a dict of words and the counts"""
    """Arguments: 
    seriesColumn: series of string 
    N: integer number top word counts to be drawn
    ignore_word_list: list of string words to be ignored in the graph """
    count_vectorizer = CountVectorizer(stop_words='english')
    count_data = count_vectorizer.fit_transform(seriesColumn)
    words = count_vectorizer.get_feature_names()
    total_counts = np.zeros(len(words))
    for t in count_data:
        total_counts+=t.toarray()[0]
    
    count_dict = (zip(words, total_counts))
    count_dict = [(i,j) for i,j in zip(words,total_counts) if i not in ignore_word_list]
    count_dict = sorted(count_dict, key=lambda x:x[1], reverse=True)[0:N]
    words = [w[0] for w in count_dict]
    counts = [w[1] for w in count_dict]
    x_pos = np.arange(len(words)) 
    
    plt.figure(2, figsize=(15, 15/1.6180))
    plt.subplot(title=str(N)+' most common words in alerts')
    sns.set_context("notebook", font_scale=1.25, rc={"lines.linewidth": 2.5})
    sns.barplot(x_pos, counts, palette='husl')
    plt.xticks(x_pos, words, rotation=90) 
    plt.xlabel('words')
    plt.ylabel('counts')
    plt.show()
    count=0
    for desc in seriesColumn:
        for w in words:
            if(w in desc):
                count=count+1
                break
    print("N=",N, "words covers ", '{:.2%}'.format(count/float(len(seriesColumn))), " of alerts")   
    return

def print_topics(model, count_vectorizer, n_top_words)->None:
    """ Helper function to print topics by LDA"""
    """Arguments: 
    model: trained LDA model
    count_vectorizer: vector of words by sklearn CountVectorizer()
    n_top_words: integer number of top topic keywords"""
    words = count_vectorizer.get_feature_names()
    for topic_idx, topic in enumerate(model.components_):
        print("\nTopic #%d:" % topic_idx)
        print(" ".join([words[i]
                        for i in topic.argsort()[:-n_top_words - 1:-1]]))
    return

def plot_wordcloud(long_string)->None:
    """This function displays a wordcloud from a text."""
    """Arguments:
    long_string: a string of text separated by comma"""
    wordcloud = WordCloud(background_color="white", max_words=5000, contour_width=3, contour_color='steelblue')
    wordcloud.generate(long_string)
    # Visualize the word cloud
    (wordcloud.to_image()).show()
    

    return
    
def ldaAlerts(seriesColumn,isGridSearch=False,number_topics=10,number_words=10,learning_decay_rate=.5):
    """This function performs an lda analysis on alerts in a json file. 
    It returns dominant topic matrix and the trained lda
    It runs a grid search and returns the best lda model if isGridSearch=True"""
    """Arguments:
    seriesColumn: series of string 
    isGridSearch: boolean field to perform grid search on LDA parameters
    number_topics (optional): number of clusters. default is 10
    number_topics (optional): number of keywords. default is 10
    learning_decay_rate (optional): LDA decay rate bw 0-1. default is .7"""
    count_vectorizer = CountVectorizer(stop_words='english')
    count_data = count_vectorizer.fit_transform(seriesColumn)
    if(isGridSearch):
        search_params = {'n_components': [3, 5, 7, 10], 'learning_decay': [.5,.7,.9]}# Init Grid Search Class
        lda = LDA(n_components=number_topics, n_jobs=-1,random_state=1)
        lda.fit(count_data)
        model = GridSearchCV(lda, param_grid=search_params)
        model.fit(count_data)  
        print("Best Modelby Grid Search : ", model.best_params_)
        number_topics = model.best_params_['n_components']
        learning_decay_rate=model.best_params_['learning_decay']
        lda = LDA(n_components=number_topics, learning_decay=learning_decay_rate,n_jobs=-1,random_state=1)
        lda.fit(count_data)
        # Print the topics found by the LDA model
        print("Topics found via best LDA:")
        print_topics(lda, count_vectorizer, number_words)
    else:
        
        lda = LDA(n_components=number_topics, learning_decay=learning_decay_rate,n_jobs=-1,random_state=1)
        lda.fit(count_data)

    lda_output = lda.transform(count_data)
    topicnames = ["Topic" + str(i) for i in range(number_topics)]
    docnames = ["Alert" + str(i) for i in range(len(seriesColumn))]
    df_document_topic = pd.DataFrame(np.round(lda_output, 2), columns=topicnames, index=docnames)
    # Get dominant topic for each document
    dominant_topic = np.argmax(df_document_topic.values, axis=1)
    df_document_topic['dominant_topic'] = dominant_topic
    return df_document_topic,lda

def displayFreqBiTriGrams(text:str,N=20)->None:
    """This function displays top 10 bigrams and trigrams in text"""
    """Arguments:
    text: string 
    N: integer numer of top freq ngrams"""
    from nltk.corpus import stopwords
    #nltk.download('stopwords') #uncomment this for the first use only
    from collections import Counter
    from nltk.util import ngrams 
    stoplist = stopwords.words('english')
    clean_word_list = [word for word in text.split() if word not in stoplist]    
    n_gram = 2
    bigrams=Counter(ngrams(clean_word_list, n_gram))
    print("Most common bigrams")
    for i,j in bigrams.most_common(N):
        print('_'.join(i), ' ',j)
    n_gram=3
    trigrams=Counter(ngrams(clean_word_list, n_gram))
    print("Most common trigrams")
    for i,j in trigrams.most_common(N):
        print('_'.join(i), ' ',j)
def addAlertsToTopology(G:nx.Graph, df:pd.DataFrame)->nx.Graph:
    """This function adds alerts semantics in df to the graph G"""
    """Arguments:
    G: networkx graph of topology
    df: pandas dataframe of alerts semantics """
    l=[]
    l.extend(G.nodes())
    for i in l:
        subset_df=df[df['deviceName']==i]
        issue_count=subset_df['issue_id'].nunique()
        problem_count=subset_df['problem_id'].nunique()
        topic_count=subset_df['Topic'].nunique()
        topics=""
        for j, t in subset_df['Topic'].items():
            if(str(t) not in topics): topics=topics+str(t)+','
        topics=topics[0:-1]
        G.nodes[i]['issue_count']=issue_count
        G.nodes[i]['problem_count']=problem_count
        G.nodes[i]['topic_count']=topic_count
        G.nodes[i]['topics']=topics
    return G

def remove_tags(text: str) -> str:
    """This function receives a text and cleans it from tags, non-alphanumeric chars""" 
    """Arguments: 
    text:string"""
    text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)
    text=TAG_RE.sub(' ', text)
    #text=text.replace('"','')
    #text=text.replace(".", "")
    #text=text.replace(",", "")
    #text=text.replace('->', "")
    #text=text.replace('-', "")
    #text=text.replace('&nbsp', "")
    #text=text.replace('&amp;', "&")
    #text = re.sub(r'\d+', '',text)
    return text
def read_clean_alerts(alerts_json_file_name:str, isGridSearch:bool)->pd.DataFrame():
    """This function receives alert json file name, a bool variable for lda grid sarch, performs lda on the titles,""" 
    "return a dataframe of alerts with dominant LDA Topic"
    """Arguments: 
        alerts_json_file_name:string
        isGridSearch:bool
    """
    df=pd.read_json("alerts.json",lines=True)
    #Read alerts dump
    df=pd.read_json("alerts.json",lines=True)
    print("There are",len(df),"alerts.")
    #Clean the column of tags
    for i,alert in df.iterrows():
        df.set_value(i,'title',remove_tags(alert['title']))
    #Get the column of interest
    seriesColumn=df['title']
    df_document_topic,lda=ldaAlerts(seriesColumn,isGridSearch)
    df.insert(len(df.columns), "Topic", 0, True)
    dominant_topic=df_document_topic['dominant_topic']
    for i in range(len(dominant_topic)):
        df.set_value(i,'Topic',dominant_topic[i])    
    return df

if __name__ == "__main__":
    #Read topology graph
    G=nx.read_graphml('LargestCC_topologyBorg.graphml')
    alerts_json_file_name="alerts.json"
    isGridSearch=False
    G=addAlertsToTopology(G,read_clean_alerts(alerts_json_file_name,isGridSearch))
    nx.write_graphml(G,'LargestCC_topologyBorgWithAlerts.graphml')
