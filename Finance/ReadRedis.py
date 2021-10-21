from redis import Redis
import json


redis_client = Redis(host="localhost", port=6379, decode_responses=True)
data = redis_client.xrange('OUTPUT_SENSORDOG_VOLUME')
if (len(data)==0) :
    print('There is no data in Redis')
else:
    tmp = json.loads(data[0][1].get("data"))

    dictForNeo4j = {};
    import pandas as pd
    df_contributors=pd.DataFrame.from_dict(tmp['contributors'])
    events = tmp["events"]
    events_leading_indicator = events["leading indicator"]
    indicators = tmp["indicators"]
    leading_indicators = indicators["leading indicator"]
    main_indicators = indicators["main indicator"]
    trailing_indicators = indicators["trailing indicator"]
    contributors = tmp["contributors"]
    all_regimes = tmp["all_regimes"]
    events_main_indicator = events["main indicator"]
    events_trailing_indicator = events["trailing indicator"]

    for y in range(len(events_leading_indicator)):
        eli = leading_indicators['' + str(y) + '']
        mi = main_indicators['' + str(y) + '']
        ti = trailing_indicators['' + str(y) + '']

        dicForNeo4jLeadingIndicators = {}
        leadingIndicatorsVolumes = {}
        leadingIndicatorsPrices = {}
        dictForNeo4jMainIndicators = {}
        mainIndicatorsVolumes = {}
        mainIndicatorsPrices = {}
        dictForNeo4jTrailingIndicators = {}
        trailingIndicatorsVolumes = {}
        trailingIndicatorsPrices = {}

        liv = 0
        lip = 0

        for leadingIndex in range(len(eli)):
            symbol = eli[leadingIndex].split(':')[3]

            if (":volume" in eli[leadingIndex]):
                leadingIndicatorsVolumes[liv] = symbol
                liv = liv + 1
            else:
                leadingIndicatorsPrices[lip] = symbol
                lip = lip + 1
        dicForNeo4jLeadingIndicators["volume"]=leadingIndicatorsVolumes
        dicForNeo4jLeadingIndicators["price"]=leadingIndicatorsPrices
        miv = 0
        mip = 0
        for mainIndex in range(len(mi)):
            symbol = mi[mainIndex].split(':')[3]
            if (":volume" in mi[mainIndex]):
                mainIndicatorsVolumes[miv] = symbol
                miv = miv + 1
            else:
                mainIndicatorsPrices[mip] = symbol
                mip = mip + 1
        dictForNeo4jMainIndicators["volume"]=mainIndicatorsVolumes
        dictForNeo4jMainIndicators["price"]=mainIndicatorsPrices
        tip = 0
        tiv = 0
        for trailingIndex in range(len(ti)):
            symbol = ti[trailingIndex].split(':')[3]
            if(":volume" in ti[trailingIndex]):
                trailingIndicatorsVolumes[tiv] = symbol
                tiv = tiv + 1
            else:
                trailingIndicatorsPrices[tip] = symbol
                tip = tip + 1
        dictForNeo4jTrailingIndicators["volume"]=trailingIndicatorsVolumes
        dictForNeo4jTrailingIndicators["price"]=trailingIndicatorsPrices

        neo4jIndicators = {}
        neo4jIndicators["leading indicators"] = dicForNeo4jLeadingIndicators
        neo4jIndicators["main indicators"] = dictForNeo4jMainIndicators
        neo4jIndicators["trailing indicators"] = dictForNeo4jTrailingIndicators
        dictForNeo4j['' + str(y) + ''] = neo4jIndicators

def __commit_transaction(entity):
        transaction = 0
        # transaction.create(entity)
        # graph.commit(transaction)
    
from py2neo import Graph, Relationship, Node

# graph_3 = Graph("bolt://localhost:7687")
graph = Graph(host='localhost', port=7687, user='neo4j', password='magi')
# graph.schema.create_index("apiCall", "fromRedis")
transaction = graph.begin()


# e="0"
# eventsNode = Node("Events", name=e) 
# transaction.create(eventsNode)


# INode = Node("Indicators", name="Leading Indicators") 
# transaction.create(eventsNode)

# relationship = Relationship(eventsNode, 'has', INode)
# transaction.create(relationship)

# VNode = Node("Type", name="Volume") 
# transaction.create(VNode)

# relationship = Relationship(INode, 'has', VNode)
# transaction.create(relationship)
# SNode = Node("Symbol", name="STMP") 
# transaction.create(SNode)

# relationship = Relationship(SNode, 'is', VNode)
# transaction.create(relationship)


       
for events in dictForNeo4j:
    print(events)
    e=""+events+""
    eventsNode = Node("Events", name=e) 
    __commit_transaction(eventsNode)
    
    
    for indicators in dictForNeo4j[events]:
          print(indicators) 
          i=""+indicators+""
          indicatorNode = Node("Indicators", name=i)
          __commit_transaction(indicatorNode)

          
          relationship = Relationship(eventsNode, 'has', indicatorNode)
          __commit_transaction(relationship)
          for indicatorType in dictForNeo4j[events][indicators]:
              print(indicatorType)
              it=""+indicatorType+""
              indicatorTypeNode = Node("Types", name=it) 
              __commit_transaction(indicatorTypeNode)
             
              relationship = Relationship(indicatorNode, 'has', indicatorTypeNode)
              __commit_transaction(relationship)
              for volumesymbol in dictForNeo4j[events][indicators][indicatorType]:
                  symbol=dictForNeo4j[events][indicators][indicatorType][volumesymbol]
                  v=""+symbol+""
                  symbolNode = Node("Symbol", name=v)
                  __commit_transaction(symbolNode)
                  
                  relationship = Relationship(symbolNode, 'is', indicatorTypeNode)
                  __commit_transaction(relationship)
                  
                  
                 
                  
