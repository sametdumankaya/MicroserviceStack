import numpy as np
from redis import Redis
import requests
import json
import networkx as nx
import pandas as pd

def ReadRedis(rediskey):
    redis_client = Redis(host="localhost", port=6379, decode_responses=True)
    data = redis_client.xrange(rediskey)
    tmp = json.loads(data[0][1].get("data"))

    dictForNeo4j = {};

    df_contributors = pd.DataFrame.from_dict(tmp['contributors'])
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
        dicForNeo4jLeadingIndicators["volume"] = leadingIndicatorsVolumes
        dicForNeo4jLeadingIndicators["price"] = leadingIndicatorsPrices
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
        dictForNeo4jMainIndicators["volume"] = mainIndicatorsVolumes
        dictForNeo4jMainIndicators["price"] = mainIndicatorsPrices
        tip = 0
        tiv = 0
        for trailingIndex in range(len(ti)):
            symbol = ti[trailingIndex].split(':')[3]
            if (":volume" in ti[trailingIndex]):
                trailingIndicatorsVolumes[tiv] = symbol
                tiv = tiv + 1
            else:
                trailingIndicatorsPrices[tip] = symbol
                tip = tip + 1
        dictForNeo4jTrailingIndicators["volume"] = trailingIndicatorsVolumes
        dictForNeo4jTrailingIndicators["price"] = trailingIndicatorsPrices

        neo4jIndicators = {}
        neo4jIndicators["leading indicators"] = dicForNeo4jLeadingIndicators
        neo4jIndicators["main indicators"] = dictForNeo4jMainIndicators
        neo4jIndicators["trailing indicators"] = dictForNeo4jTrailingIndicators
        neo4jIndicators["event type"] = tmp["events"]["event type (percent change)"][str(y)]
        dictForNeo4j['' + str(y) + ''] = neo4jIndicators
    dictForNeo4j["contributors"]=tmp['contributors']
    dictForNeo4j["metadata"] = tmp['metadata']
    dictForNeo4j["all_regimes"] = tmp['all_regimes']
    dictForNeo4j["Analyzed"] = tmp['Analyzed']
    InsertNeo4j(dictForNeo4j)
def InsertNeo4j(dictForNeo4j):

    financeNode = InsertNode("Finance", "L2.3", "Finance")
    stockMarketNode = InsertNode("Stock Market", "L2.3", "Stock Market")
    companyNode = InsertNode("Company", "L2.3", "Company")
    RelationshipAsym(companyNode, 'in', stockMarketNode)
    sectorNode = InsertNode("Sector", "L2.2", "Sector")
    industryNode = InsertNode("Industry", "L2.2", "Industry")
    nasdaqNode = InsertNode("Nasdaq", "L2.2", "Nasdaq")
    RelationshipAsym(sectorNode, 'has', industryNode)
    AddIntension(sectorNode, financeNode)
    AddIntension(industryNode, financeNode)
    AddIntension(nasdaqNode, stockMarketNode)



    G = nx.read_graphml('finL2Extension.graphml')
    all_nodes = pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index')
    sectorDicts = {}
    industryDicts = {}
    symbolDicts = {}
    for index, row in all_nodes.iterrows():
        sectorName = row["sector"]
        symbolName = row["symbol"]
        industryName = row['industry']

        if symbolName is not np.nan and sectorName is not np.nan and industryName is not np.nan:
            if sectorName not in sectorDicts :
                innerSectorNode = InsertNode("Sector", "L2.1", sectorName)
                AddIntension(innerSectorNode, sectorNode)
                if innerSectorNode > 0:
                    sectorDicts[sectorName] =innerSectorNode

            if industryName not in industryDicts :
                innerIndustryNode = InsertNode("Industry", "L2.1", industryName)
                if innerIndustryNode > 0:
                    industryDicts[industryName] = innerIndustryNode
                    AddIntension(innerIndustryNode, industryNode)
                    RelationshipAsym(sectorDicts[sectorName], 'has', innerIndustryNode)

            innerSymbolNode = InsertNode("Company", "L2.1", symbolName)
            symbolDicts[symbolName] =innerSymbolNode
            AddIntension(innerSymbolNode, companyNode)
            AddIntension(innerSymbolNode, nasdaqNode)
            RelationshipAsym(innerSymbolNode, 'has', industryDicts[industryName])
            RelationshipAsym(innerSymbolNode, 'has', sectorDicts[sectorName])

    timeSeriesNode = InsertNode("TimeSeries", "L2.3", "TimeSeries")
    eventNodeMain = InsertNode("Event", "L2.2", "Event")
    AddIntension(eventNodeMain, timeSeriesNode)
    indicatorsMain = InsertNode("Indicator", "L2.2", "Indicator")
    RelationshipAsym(eventNodeMain, 'has', indicatorsMain)
    financialEventNode = InsertNode("Financial Event", "L2.1", "Financial Event")
    AddIntension(financialEventNode, eventNodeMain)
    regimeNode = InsertNode("Regime", "L2.1", "Regime")
    analyzedNode = InsertNode("Analyzed", "L2.1", "Analyzed")
    AddIntension(analyzedNode, timeSeriesNode)
    metadataNode = InsertNode("Metadata", "L2.1", "Metadata")
    RelationshipAsym(analyzedNode, 'has', metadataNode)
    RelationshipAsym(analyzedNode, 'has', regimeNode)

    liNode = InsertNode("Li", "L2.1", "Li")
    miNode = InsertNode("Mi", "L2.1", "Mi")
    tiNode = InsertNode("Ti", "L2.1", "Ti")

    AddIntension(liNode, indicatorsMain)
    AddIntension(miNode, indicatorsMain)
    AddIntension(tiNode, indicatorsMain)

    volumeEventNode = InsertNode("Volume Event", "L2.0", "Volume Event")
    AddIntension(volumeEventNode, financialEventNode)
    priceEventNode = InsertNode("Price Event", "L2.0", "Price Event")
    AddIntension(priceEventNode, financialEventNode)
    gainEventNode = InsertNode("Gain Event", "L2.0", "Gain Event")
    AddIntension(gainEventNode, financialEventNode)
    lossEventNode = InsertNode("Loss Event", "L2.0", "Loss Event")
    AddIntension(lossEventNode, financialEventNode)
    predictorNode = InsertNode("Predictor", "L2.0", "Predictor")
    RelationshipAsym(priceEventNode, 'has', predictorNode)
    RelationshipAsym(volumeEventNode, 'has', predictorNode)


    paramsNode = InsertNode("Params", "L1", "Params")
    AddIntension(paramsNode, metadataNode)

    for params in dictForNeo4j['metadata']['parameters']:
        prmNodeName = params +" = " + str( dictForNeo4j['metadata']['parameters'][params])
        prmNode =InsertNode("Params", "L1", prmNodeName)
        RelationshipAsym(paramsNode, 'has', prmNode)

    regimeDicts = {}
    count = 0
    for regime in dictForNeo4j['all_regimes']:
        regimeList = regime
        innerRegimeNode = InsertNode("Regime", "L1", regimeList)
        regimeDicts[count] = innerRegimeNode
        count = count + 1
        AddIntension(innerRegimeNode, regimeNode)


    for events in dictForNeo4j:
        print(events)
        e = "Event" + events + ""
        eventNode=InsertNode("Event" , "L1", e)

        if(dictForNeo4j[events]["event type"] == "increase"):
            AddIntension(eventNode, gainEventNode)
        else:
            AddIntension(eventNode, lossEventNode)

        for indicators in dictForNeo4j[events]:
            if indicators != "event type":

                for indicatorType in dictForNeo4j[events][indicators]:
                    if indicatorType =="volume":
                        AddIntension(eventNode, volumeEventNode)

                    else:
                        AddIntension(eventNode, priceEventNode)
                    it = "" + indicatorType + ""
                    for volumesymbol in dictForNeo4j[events][indicators][indicatorType]:
                        symbol = dictForNeo4j[events][indicators][indicatorType][volumesymbol]
                        symbolName = "" + symbol + ""
                        symbolNode = InsertNode(indicators, "L1", symbolName,it)
                        l = [dictForNeo4j["Analyzed"].index(i) for i in dictForNeo4j["Analyzed"] if ':'+symbolName+':' in i]
                        if l[0] in regimeDicts:
                            RelationshipAsym(symbolNode, 'has', regimeDicts[l[0]])
                        AddIntension(symbolNode, analyzedNode)
                        if indicators == 'leading indicator':
                            AddIntension(symbolNode, liNode)
                        if indicators == 'main indicator':
                            AddIntension(symbolNode, miNode)
                        if indicators == 'trailing indicator':
                            AddIntension(symbolNode, tiNode)

                        # Controlling symbol name from graphml list
                        if symbol in symbolDicts:
                            AddIntension(symbolNode, symbolDicts[symbol])
                        else:
                            print("Not in: ",symbol)

                        RelationshipAsym(eventNode, 'has', symbolNode)
                        dictEventContributor = {key: value for (key, value) in dictForNeo4j["contributors"]["event"].items() if value == (int(events)+1) }
                        dictEventIndicator = {key: value for (key, value) in dictForNeo4j["contributors"]["indicator"].items() if value.split(':')[3] == symbolName }

                        for cnt in dictEventContributor:
                           for Ind in dictEventIndicator:
                               if cnt== Ind:
                                   contributeNode = InsertNode(indicators, "L1", symbolName +":Event"+events  )
                                   RelationshipAsym(symbolNode, 'contributes', contributeNode)
                                   AddIntension(contributeNode, predictorNode)


def InsertNode(label,level,properties,type=""):
    params= {
             "name": label,
             "level": level,
             "properties": {
                "name": properties,
                "type":type
     }
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    url = "http://localhost:8003/create_node/"
    r = requests.post(url, data=json.dumps(params), headers=headers)
    return json.loads(r.content.decode("utf-8"))["node_id"]
def Relationship(startNode ,relation,endNode):
    params = {
        "start_node_id": startNode,
        "end_node_id": endNode,
        "relation_name":relation,
        "relation_properties": {
        }
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    url = "http://localhost:8003/add_symmetric_relation/"
    r = requests.post(url, data=json.dumps(params), headers=headers)
    return r

def RelationshipAsym(startNode, relation, endNode):
    params = {
        "start_node_id": startNode,
        "end_node_id": endNode,
        "relation_name": relation,
        "relation_properties": {
        }
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    url = "http://localhost:8003/add_antisymmetric_relation/"
    r = requests.post(url, data=json.dumps(params), headers=headers)
    return r

def AddIntension(startNode, endNode):
    params = {
        "start_node_id": startNode,
        "end_node_id": endNode,
        "relation_properties": {
        }
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    url = "http://localhost:8003/add_intension/"
    r = requests.post(url, data=json.dumps(params), headers=headers)
    return r

def AddExtension(startNode, endNode):
    params = {
        "start_node_id": startNode,
        "end_node_id": endNode,
        "relation_properties": {
        }
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    url = "http://localhost:8003/add_extension/"
    r = requests.post(url, data=json.dumps(params), headers=headers)
    return r

