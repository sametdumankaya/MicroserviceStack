import json
from datetime import datetime
import numpy as np
import pandas as pd
import time
import nltk


class FinanceUtils:
    def __init__(self, redis_client, neo4j_api_client,msig_api_client,news_utils):
        self.redis_client = redis_client
        self.neo4j_api_client = neo4j_api_client
        self.msig_api_client = msig_api_client
        self.news_utils  = news_utils


    def create_json_via_redis(self, redis_name: str):
        data = self.redis_client.xrevrange(redis_name, count=1)
        from datetime import  timedelta
        if data is None or len(data) == 0:
            return "No output data available."
        news_date=""
        x = datetime.today()
        weekday = x.weekday()
        if weekday == 5 or weekday == 6:  # saturday/sunday
            pass
        else:
            delta = 1
            if weekday == 0:  # monday
                delta = 3
            news_date = (datetime.today() - timedelta(days=delta)).strftime('%Y-%m-%d 13:30:01.0')

        news_analyzed_result = self.news_utils.getNewsFromRedis(10,news_date)

        positive_symbol_list= news_analyzed_result["posNews"]
        negative_symbol_list = news_analyzed_result["negNews"]

        # Since only the last element is queried with xrevrange above, we can process the 0th element
        output_data_dict = json.loads(data[0][1]["data"])
        loop_no = output_data_dict["metadata"]["loop_no"]

        json_for_neo4j = {"nodes": [], "relation_triplets": []}

        index = 0
        json_for_neo4j["nodes"].append(
            {'name': "Time Series", 'index': index, 'level': "L2.3",  'properties': {}})
        time_series_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Event", 'index': index, 'level': "L2.2", 'properties': {}})
        event_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Indicator", 'index': index, 'level': "L2.2", 'properties': {}})
        indicator_index = index
        index = index + 1
        
        json_for_neo4j["nodes"].append({'name': "Unclassified Event", 'index': index, 'level': "L2.1", 'properties': {}})
        unclassified_event_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Classified Event", 'index': index, 'level': "L2.1",  'properties': {}})
        classified_event_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Analyzed", 'index': index, 'level': "L2.0",  'properties': {}})
        analyzed_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Metadata", 'index': index, 'level': "L2.0",  'properties': {}})
        metadata_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Regime", 'index': index, 'level': "L2.0",  'properties': {}})
        regime_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Li", 'index': index, 'level': "L2.0",  'properties': {}})
        li_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Ti", 'index': index, 'level': "L2.0",  'properties': {}})
        ti_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Mi", 'index': index, 'level': "L2.0",  'properties': {}})
        mi_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Square Wave", 'index': index, 'level': "L2.0",  'properties': {}})
        # line_ts_node_id = self.neo4j_api_client.create_node(line_ts, "L1")
        square_wave_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Volume Event", 'index': index, 'level': "L2.0",  'properties': {}})
        volume_event_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Price Event", 'index': index, 'level': "L2.0",  'properties': {}})
        price_event_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Predictor", 'index': index, 'level': "L2.0",  'properties': {}})
        predictor_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Spike", 'index': index, 'level': "L2.0",  'properties': {}})
        spike_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Line", 'index': index, 'level': "L2.0",  'properties': {}})
        line_index = index
        index = index + 1

        json_for_neo4j["relation_triplets"].append([event_index, 'intension', time_series_index, {}])
        json_for_neo4j["relation_triplets"].append([event_index, 'has', indicator_index, {}])
        json_for_neo4j["relation_triplets"].append([classified_event_index, 'intension', event_index, {}])
        json_for_neo4j["relation_triplets"].append([unclassified_event_index, 'intension', event_index, {}])
        json_for_neo4j["relation_triplets"].append([analyzed_index, 'intension', time_series_index, {}])
        json_for_neo4j["relation_triplets"].append([analyzed_index, 'has', metadata_index, {}])
        json_for_neo4j["relation_triplets"].append([analyzed_index, 'has', regime_index, {}])
        json_for_neo4j["relation_triplets"].append([li_index, 'intension', indicator_index, {}])
        json_for_neo4j["relation_triplets"].append([mi_index, 'intension', indicator_index, {}])
        json_for_neo4j["relation_triplets"].append([ti_index, 'intension', indicator_index, {}])
        json_for_neo4j["relation_triplets"].append([price_event_index, 'intension', unclassified_event_index, {}])
        json_for_neo4j["relation_triplets"].append([volume_event_index, 'intension', unclassified_event_index, {}])
        json_for_neo4j["relation_triplets"].append([volume_event_index, 'has', predictor_index, {}])
        json_for_neo4j["relation_triplets"].append([price_event_index, 'has', predictor_index, {}])
        json_for_neo4j["relation_triplets"].append([square_wave_index, 'intension', time_series_index, {}])
        json_for_neo4j["relation_triplets"].append([spike_index, 'intension', time_series_index, {}])
        json_for_neo4j["relation_triplets"].append([line_index, 'intension', time_series_index, {}])

        # line ts
        for line_ts in output_data_dict["Line"]:
            json_for_neo4j["nodes"].append({'name':line_ts,'index':index,'level':'L1','properties':{}})

            json_for_neo4j["relation_triplets"].append([index, 'intension', line_index, {}])
            index = index + 1


        # spike ts
        for spike_ts in output_data_dict["Spike"]:
            json_for_neo4j["nodes"].append({'name': spike_ts, 'index': index, 'level': 'L1',  'properties': {}})

            json_for_neo4j["relation_triplets"].append([index, 'intension', spike_index, {}])
            index = index + 1

        # square ts
        for square_ts in output_data_dict["Square"]:
            json_for_neo4j["nodes"].append({'name': square_ts, 'index': index, 'level': 'L1',  'properties': {}})

            json_for_neo4j["relation_triplets"].append([index, 'intension', square_wave_index, {}])
            index = index + 1

        # analysis parameters
        metadata_dict = output_data_dict["metadata"]["parameters"]
        metadata_dict["start_ts"] = str(output_data_dict["metadata"]["start_ts"])
        metadata_dict["end_ts"] = str(output_data_dict["metadata"]["end_ts"])
        metadata_dict["min_ts"] = str(output_data_dict["metadata"]["min_ts"])
        metadata_dict["max_ts"] = str(output_data_dict["metadata"]["max_ts"])
        metadata_dict["filters"] = ','.join(metadata_dict["filters"])

        json_for_neo4j["nodes"].append({'name': "params", 'index': index, 'level': 'L1',  'properties': metadata_dict})

        json_for_neo4j["relation_triplets"].append([index, 'intension', metadata_index, {}])
        index = index+1



        temp_analyzed_dict = {}
        # analyzed together with regimes
        for idx, analyze in enumerate(output_data_dict["Analyzed"]):

            analyze_name = analyze.split(':')[3]

            if analyze_name in positive_symbol_list or analyze_name in negative_symbol_list:
                curr_analyzed_index = index
                json_for_neo4j["nodes"].append(
                    {'name': analyze_name, 'index': index, 'level': 'L1',  'properties': {}})
                index = index + 1

                temp_analyzed_dict[analyze_name] = curr_analyzed_index

                json_for_neo4j["nodes"].append(
                    {'name': analyze_name, 'index': index, 'level': 'L2.1',  'properties': {}})

                json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'intension', index, {}])
                index = index + 1

                json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'intension', analyzed_index, {}])

                if idx<len(output_data_dict["all_regimes"]):
                    millisecond_regimes = output_data_dict["all_regimes"][idx]
                    curr_regime_index= index
                    json_for_neo4j["nodes"].append(
                        {'name': f"Regime{loop_no}_{idx + 1}", 'index': index, 'level': 'L1',  'properties': {
                        "regime": ",".join([str(x) for x in millisecond_regimes])
                    }})

                    index = index + 1
                    json_for_neo4j["relation_triplets"].append([curr_regime_index, 'intension', regime_index, {}])
                    json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_regime_index, {}])



        # events
        for idx in range(len(output_data_dict["indicators"]["leading indicator"])):

            json_for_neo4j["nodes"].append(
                {'name': f"Event{loop_no}_{idx + 1}", 'index': index, 'level': 'L1',  'properties': {}})
            curr_event_index = index
            if redis_name == 'MAGI_VOLUME':
                json_for_neo4j["relation_triplets"].append([curr_event_index, 'intension', volume_event_index, {}])
            else:
                json_for_neo4j["relation_triplets"].append([curr_event_index, 'intension', price_event_index, {}])


            json_for_neo4j["relation_triplets"].append([curr_event_index, 'intension', unclassified_event_index, {}])

            index = index + 1
            event_leading_indicator_list = output_data_dict["indicators"]["leading indicator"][str(idx)]
            event_main_indicator_list = output_data_dict["indicators"]["main indicator"][str(idx)]
            event_trailing_indicator_list = output_data_dict["indicators"]["trailing indicator"][str(idx)]

            temp_indicator_dict = {}
            for leading_indicator in event_leading_indicator_list:
                analyzed_name= leading_indicator.split(':')[3]

                if analyze_name in positive_symbol_list or analyze_name in negative_symbol_list:
                    li_name = analyzed_name + f"_Event{loop_no}_{idx + 1}"

                    json_for_neo4j["nodes"].append({
                        "name": li_name,
                        "level": "L1",
                        "index": index,
                        "properties": {}
                    })
                    curr_li_index = index
                    index = index+1

                    temp_indicator_dict[li_name] = curr_li_index

                    json_for_neo4j["relation_triplets"].append([curr_event_index, 'has', curr_li_index, {}])
                    json_for_neo4j["relation_triplets"].append([curr_li_index, 'intension', li_index, {}])
                    curr_analyzed_index = temp_analyzed_dict[analyzed_name]
                    json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_li_index, {}])



            for main_indicator in event_main_indicator_list:
                analyzed_name = main_indicator.split(':')[3]

                if analyze_name in positive_symbol_list or analyze_name in negative_symbol_list:

                    mi_name =analyzed_name  + f"Event{loop_no}_{idx + 1}"

                    curr_mi = None
                    if (mi_name in temp_indicator_dict):
                        curr_mi = temp_indicator_dict.key(mi_name)

                    if curr_mi is None:
                        json_for_neo4j["nodes"].append({
                            "name": mi_name,
                            "level": "L1",
                            "index": index,
                            "properties": {}
                        })
                        curr_mi_index = index
                        index = index + 1
                    else:
                        curr_mi_index = curr_mi["index"]



                    json_for_neo4j["relation_triplets"].append([curr_event_index, 'has', curr_mi_index, {}])
                    json_for_neo4j["relation_triplets"].append([curr_mi_index, 'intension', mi_index, {}])
                    curr_analyzed_index = temp_analyzed_dict[analyzed_name]
                    json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_mi_index, {}])


            for trailing_indicator in event_trailing_indicator_list:
                analyzed_name = trailing_indicator.split(':')[3]

                if analyze_name in positive_symbol_list or analyze_name in negative_symbol_list:

                    ti_name =analyzed_name  + f"Event{loop_no}_{idx + 1}"

                    curr_ti = None
                    if (ti_name in temp_indicator_dict):
                        curr_ti = temp_indicator_dict.key(ti_name)

                    if curr_ti is None:
                        json_for_neo4j["nodes"].append({
                            "name": ti_name,
                            "level": "L1", 'id': 0,
                            "index": index,
                            "properties": {}
                        })
                        curr_ti_index = index
                        index = index + 1

                    else:
                        curr_ti_index = curr_ti["index"]



                    json_for_neo4j["relation_triplets"].append([curr_event_index, 'has', curr_ti_index, {}])
                    json_for_neo4j["relation_triplets"].append([curr_ti_index, 'intension', ti_index, {}])
                    curr_analyzed_index = temp_analyzed_dict[analyzed_name]
                    json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_ti_index, {}])



        # contributors
        if len(output_data_dict["contributors"]) >0:
            for key in output_data_dict["contributors"]["event"]:
                value = output_data_dict["contributors"]["event"][key]
                if value != "no_event":
                    # create contributions
                    contributor_name = output_data_dict["contributors"]["indicator"][key].split(':')[3]
                    contribution_amount = output_data_dict["contributors"]["contribution"][key]

                    contributor = next(
                        (node for node in json_for_neo4j["nodes"] if node["name"] == contributor_name and node["level"] == "L1"),
                        None)

                    if contributor is not None:
                        contributor_ts_node_index = contributor["index"]

                        json_for_neo4j["nodes"].append(
                            {'name': f"{contributor_name}:Event{loop_no}_{value}", 'index': index, 'level': 'L1',  'properties': {}})

                        json_for_neo4j["relation_triplets"].append([index, 'intension', predictor_index, {}])
                        json_for_neo4j["relation_triplets"].append([contributor_ts_node_index, 'contributes', index, {}])
                        index = index + 1

                # TODO
                #         # create follows temporally relations
                #         contributed_event_node_id = self.neo4j_api_client.find_node_id(f"Event{loop_no}_{value}", "L1")
                #         how_long = ""
                #
                #         if output_data_dict["events"]["leading indicator"][str(value)] is not None or \
                #                 output_data_dict["events"]["leading indicator"][str(value)] != "Unknown":
                #             d1 = datetime.strptime(output_data_dict["events"]["leading indicator"][str(value)],
                #                                    '%Y-%m-%d %H:%M:%S')
                #             d2 = datetime.strptime(output_data_dict["events"]["main indicator"][str(value)],
                #                                    '%Y-%m-%d %H:%M:%S')
                #             how_long = (d2 - d1).total_seconds() * 1000
                #         self.neo4j_api_client.follows_temporally(contributed_event_node_id, contributor_ts_node_id, how_many=1,
                #                                                  how_long=f"{str(how_long)} ms",
                #                                                  contribution_amount=contribution_amount)"]


        return json_for_neo4j

    def getMarketCapitalPerEvent(self, all_ts, all_data, events, indicators,df_price_data,df_volume_data):

        # MARKET CAPITAL ESTIMATION
        market_dict = []
        df_price_data =json.loads(df_price_data)
        df_price_data =pd.DataFrame(df_price_data)

        df_volume_data = json.loads(df_volume_data)
        df_volume_data = pd.DataFrame(df_volume_data)

        for t in indicators["leading indicator"]:
            li_list = indicators["leading indicator"][t]
            mi_list = indicators["main indicator"][t]
            ti_list = indicators["trailing indicator"][t]

            li_dt = datetime.strptime(events["leading indicator"][t],"%Y-%m-%d %H:%M:%S")
            mi_dt = datetime.strptime(events["main indicator"][t], "%Y-%m-%d %H:%M:%S")
            ti_dt = datetime.strptime(events["trailing indicator"][t], "%Y-%m-%d %H:%M:%S")

            li_ts = datetime.timestamp(li_dt) *1000
            mi_ts = datetime.timestamp(mi_dt) * 1000
            ti_ts = datetime.timestamp(ti_dt) *1000
            for tckr in li_list:  # market capital for leading indicators
                try:
                    col_index = list(df_price_data.columns).index(tckr.replace("volume","price"))
                    if len(all_data["metadata"]["ts_all"]) > col_index:
                        if (li_ts in all_data["metadata"]["ts_all"][col_index]):
                            ts_non_align_index = all_data["metadata"]["ts_all"][col_index].index(li_ts)
                        else:
                            ts_non_align_index = len(all_data["metadata"]["ts_all"][col_index]) - 1


                        if(len(df_price_data[tckr.replace("volume","price")])>ts_non_align_index):
                            market_dict.append({"event_number":int(t)+ 1, "symbol": tckr.split(':')[3],
                                                "price": np.nan_to_num(df_price_data[tckr.replace("volume","price")][ts_non_align_index]),
                                                "volume": np.nan_to_num(df_volume_data[tckr.replace("price","volume")][ts_non_align_index]),
                                                "market_capital": np.nan_to_num(
                                                    df_price_data[tckr.replace("volume","price")][ts_non_align_index]) * np.nan_to_num(
                                                    df_volume_data[tckr.replace("price","volume")][ts_non_align_index]),
                                                "indicator_type": "leading indicator"})
                except:
                    print("x")
            for tckr in mi_list:  # market capital for main indicators
                try:
                    col_index = list(df_price_data.columns).index(tckr.replace("volume","price"))
                    if len(all_data["metadata"]["ts_all"]) > col_index:
                        if (mi_ts in all_data["metadata"]["ts_all"][col_index]):
                            ts_non_align_index = all_data["metadata"]["ts_all"][col_index].index(mi_ts)
                        else:
                            ts_non_align_index = len(all_data["metadata"]["ts_all"][col_index]) - 1
                        if (len(df_price_data[tckr.replace("volume", "price")]) > ts_non_align_index and len(df_volume_data[tckr.replace("price", "volume")]) > ts_non_align_index):
                            market_dict.append({"event_number": int(t) + 1, "symbol": tckr.split(':')[3],
                                                "price": np.nan_to_num(df_price_data[tckr.replace("volume","price")][ts_non_align_index]),
                                                "volume": np.nan_to_num(df_volume_data[tckr.replace("price","volume")][ts_non_align_index]),
                                                "market_capital": np.nan_to_num(
                                                    df_price_data[tckr.replace("volume","price")][ts_non_align_index]) * np.nan_to_num(
                                                    df_volume_data[tckr.replace("price","volume")][ts_non_align_index]),
                                                "indicator_type": "main indicator"})
                except:
                    print("y")
            for tckr in ti_list:  # market capital for trailing indicators
                try:
                    col_index = list(df_price_data.columns).index(tckr.replace("volume","price"))
                    if len(all_data["metadata"]["ts_all"]) > col_index:
                        if (ti_ts in all_data["metadata"]["ts_all"][col_index]):
                            ts_non_align_index = all_data["metadata"]["ts_all"][col_index].index(ti_ts)
                        else:
                            ts_non_align_index = len(all_data["metadata"]["ts_all"][col_index]) - 1

                        if (len(df_price_data[tckr.replace("volume", "price")]) > ts_non_align_index and len(df_volume_data[tckr.replace("price", "volume")]) > ts_non_align_index):
                            market_dict.append({"event_number": int(t) + 1, "symbol": tckr.split(':')[3],
                                                "price": np.nan_to_num(df_price_data[tckr.replace("volume","price")][ts_non_align_index]),
                                                "volume": np.nan_to_num(df_volume_data[tckr.replace("price","volume")][ts_non_align_index]),
                                                "market_capital": np.nan_to_num(
                                                    df_price_data[tckr.replace("volume","price")][ts_non_align_index]) * np.nan_to_num(
                                                    df_volume_data[tckr.replace("price","volume")][ts_non_align_index]),
                                                "indicator_type": "trailing indicator"})
                except:
                    print("z")

        df_market_capital_price = pd.DataFrame(market_dict)
        return df_market_capital_price

    def getMarketCapitalPerEvent_v2(self, all_data, events_price, indicators_price):

        # MARKET CAPITAL ESTIMATION
        market_dict = []
        for i, r in indicators_price.iterrows():
            li_list = r["leading indicator"]
            mi_list = r["main indicator"]
            ti_list = r["trailing indicator"]

            li_dt = datetime.strptime(events_price["leading indicator"][i], "%Y-%m-%d %H:%M:%S")
            mi_dt = datetime.strptime(events_price["main indicator"][i], "%Y-%m-%d %H:%M:%S")
            ti_dt = datetime.strptime(events_price["trailing indicator"][i], "%Y-%m-%d %H:%M:%S")

            li_ts = datetime.timestamp(li_dt) * 1000
            mi_ts = datetime.timestamp(mi_dt) * 1000
            ti_ts = datetime.timestamp(ti_dt) * 1000


            for tckr in li_list:  # market capital for leading indicators
                tckr = tckr.split(':')[3]
                col_index = list(all_data["df_price_data"].columns).index(tckr)
                if len(all_data["ts_price"]) > col_index:
                    if (li_ts in all_data["ts_price"][col_index]):
                        ts_non_align_index = all_data["ts_price"][col_index].index(li_ts)
                    else:
                        ts_non_align_index = len(all_data["ts_price"][col_index]) - 1
                    price = np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index])
                    volume = np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index])
                    market_dict.append({"event_number": int(i) + 1, "symbol": tckr,
                                        "price": price,
                                        "market_capital": price * volume,
                                        "volume": volume,
                                        "indicator_type": "leading indicator"})
            for tckr in mi_list:  # market capital for main indicators
                tckr = tckr.split(':')[3]
                col_index = list(all_data["df_price_data"].columns).index(tckr)
                if len(all_data["ts_price"]) > col_index:
                    if (mi_ts in all_data["ts_price"][col_index]):
                        ts_non_align_index = all_data["ts_price"][col_index].index(mi_ts)
                    else:
                        ts_non_align_index = len(all_data["ts_price"][col_index]) - 1

                    price = np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index])
                    volume = np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index])
                    market_dict.append({"event_number": int(i) + 1, "symbol": tckr,
                                        "price": price,
                                        "market_capital": price * volume,
                                        "volume": volume,
                                        "indicator_type": "main indicator"})
            for tckr in ti_list:  # market capital for trailing indicators
                tckr = tckr.split(':')[3]
                col_index = list(all_data["df_price_data"].columns).index(tckr)
                if len(all_data["ts_price"]) > col_index:
                    if (ti_ts in all_data["ts_price"][col_index]):
                        ts_non_align_index = all_data["ts_price"][col_index].index(ti_ts)
                    else:
                        ts_non_align_index = len(all_data["ts_price"][col_index]) - 1
                    price = np.nan_to_num(all_data["df_price_data"][tckr][ts_non_align_index])
                    volume = np.nan_to_num(all_data["df_volume_data"][tckr][ts_non_align_index])
                    market_dict.append({"event_number": int(i) + 1, "symbol": tckr,
                                        "price":price,
                                        "market_capital": price * volume,
                                        "volume": volume,
                                        "indicator_type": "trailing indicator"})

        df_market_capital_price = pd.DataFrame(market_dict)
        return df_market_capital_price

    def getSectorIndustryPerEvent(self,indicators, L2name):
        # SECTORS
        import networkx as nx
        G = nx.read_graphml(L2name)
        li_industries = []
        li_sectors = []
        mi_industries = []
        mi_sectors = []
        ti_industries = []
        ti_sectors = []


        for t in indicators["leading indicator"]:
            tmp_li_ind = []
            tmp_li_sect = []
            for i in indicators["leading indicator"][t]:
                symbol = i.split(':')[3]
                if (symbol in list(G.nodes())):
                    subg = nx.ego_graph(G, symbol, 1).nodes(data=True)
                    for n in subg:
                        if (len(n) > 1):
                            if ('industry' in n[1].keys()):
                                tmp_li_ind.append(n[1]["industry"])
                            if ('sector' in n[1].keys()):
                                tmp_li_sect.append(n[1]["sector"])

            tmp_li_ind = list(dict.fromkeys(tmp_li_ind))
            tmp_li_sect = list(dict.fromkeys(tmp_li_sect))
            li_industries.append(tmp_li_ind)
            li_sectors.append(tmp_li_sect)


        for t in indicators["main indicator"]:
            tmp_mi_ind = []
            tmp_mi_sect = []
            for i in indicators["main indicator"][t]:
                symbol = i.split(':')[3]
                if (symbol in list(G.nodes())):
                    subg = nx.ego_graph(G, symbol, 1).nodes(data=True)
                    for n in subg:
                        if (len(n) > 1):
                            if ('industry' in n[1].keys()):
                                tmp_mi_ind.append(n[1]["industry"])
                            if ('sector' in n[1].keys()):
                                tmp_mi_sect.append(n[1]["sector"])

            tmp_mi_ind = list(dict.fromkeys(tmp_mi_ind))
            tmp_mi_sect = list(dict.fromkeys(tmp_mi_sect))
            mi_industries.append(tmp_mi_ind)
            mi_sectors.append(tmp_mi_sect)



        for t in indicators["trailing indicator"]:
            tmp_ti_ind = []
            tmp_ti_sect = []
            for i in indicators["trailing indicator"][t]:
                symbol = i.split(':')[3]
                if (symbol in list(G.nodes())):
                    subg = nx.ego_graph(G, symbol, 1).nodes(data=True)
                    for n in subg:
                        if (len(n) > 1):
                            if ('industry' in n[1].keys()):
                                tmp_ti_ind.append(n[1]["industry"])
                            if ('sector' in n[1].keys()):
                                tmp_ti_sect.append(n[1]["sector"])


            tmp_ti_ind = list(dict.fromkeys(tmp_ti_ind))
            tmp_ti_sect = list(dict.fromkeys(tmp_ti_sect))
            ti_industries.append(tmp_ti_ind)
            ti_sectors.append(tmp_ti_sect)


        df_sectors = pd.DataFrame({"li_sectors": li_sectors, "mi_sectors": mi_sectors, "ti_sectors": ti_sectors})
        df_industries = pd.DataFrame(
            {"li_industries": li_industries, "mi_industries": mi_industries, "ti_industries": ti_industries})
        return df_sectors, df_industries

    def getSectorIndustryPerEvent_v2(self,indicators_price, L2name):
        # SECTORS
        import networkx as nx
        G = nx.read_graphml(L2name)
        li_industries = []
        li_sectors = []
        mi_industries = []
        mi_sectors = []
        ti_industries = []
        ti_sectors = []
        for i, r in indicators_price.iterrows():
            tmp_li_ind = []
            tmp_li_sect = []
            for t in r["leading indicator"]:
                t = t.split(":")
                if len(t) >= 3:
                    t = t[3]
                else:
                    t = t[0]
                if (t in list(G.nodes())):
                    subg = nx.ego_graph(G, t, 1).nodes(data=True)
                    for n in subg:
                        if (len(n) > 1):
                            if ('industry' in n[1].keys()):
                                tmp_li_ind.append(n[1]["industry"])
                            if ('sector' in n[1].keys()):
                                tmp_li_sect.append(n[1]["sector"])

            tmp_li_ind = list(dict.fromkeys(tmp_li_ind))
            tmp_li_sect = list(dict.fromkeys(tmp_li_sect))

            tmp_mi_ind = []
            tmp_mi_sect = []
            for t in r["main indicator"]:
                if (t in list(G.nodes())):
                    subg = nx.ego_graph(G, t, 1).nodes(data=True)
                    for n in subg:
                        if (len(n) > 1):
                            if ('industry' in n[1].keys()):
                                tmp_mi_ind.append(n[1]["industry"])
                            if ('sector' in n[1].keys()):
                                tmp_mi_sect.append(n[1]["sector"])
            tmp_mi_ind = list(dict.fromkeys(tmp_mi_ind))
            tmp_mi_sect = list(dict.fromkeys(tmp_mi_sect))

            tmp_ti_ind = []
            tmp_ti_sect = []
            for t in r["trailing indicator"]:
                if (t in list(G.nodes())):
                    subg = nx.ego_graph(G, t, 1).nodes(data=True)
                    for n in subg:
                        if (len(n) > 1):
                            if ('industry' in n[1].keys()):
                                tmp_ti_ind.append(n[1]["industry"])
                            if ('sector' in n[1].keys()):
                                tmp_ti_sect.append(n[1]["sector"])
            tmp_ti_ind = list(dict.fromkeys(tmp_ti_ind))
            tmp_ti_sect = list(dict.fromkeys(tmp_ti_sect))
            li_industries.append(tmp_li_ind)
            li_sectors.append(tmp_li_sect)
            mi_industries.append(tmp_mi_ind)
            mi_sectors.append(tmp_mi_sect)
            ti_industries.append(tmp_ti_ind)
            ti_sectors.append(tmp_ti_sect)

        df_sectors = pd.DataFrame({"li_sectors": li_sectors, "mi_sectors": mi_sectors, "ti_sectors": ti_sectors})
        df_industries = pd.DataFrame(
            {"li_industries": li_industries, "mi_industries": mi_industries, "ti_industries": ti_industries})
        return df_sectors, df_industries

    def sendNewsToFrontEnd(self,msig_data, df_market_capital_price, df_market_capital_volume,
                           url='http://localhost:5000/Events/PostEvents', num_events_price_gain=0,
                           num_events_volume_gain=0, isStartofDay=False):
        import json
        import requests
        from datetime import datetime
        import pytz
        import redis
        import pandas as pd
        import pickle
        redis_msig = redis.Redis(host='localhost', port=6379)
        df_company_news = pd.DataFrame()
        df_company_daily_news = pd.DataFrame()
        df_curated_news = pd.DataFrame()
        if (redis_msig.ping()):
            tmp_data = redis_msig.lpop("NewsCompany")
            if tmp_data != None:
                redis_msig.lpush("NewsCompany", tmp_data)
                if (len(tmp_data) > 0):
                    tmp_data = pickle.loads(tmp_data)
                    # if(tmp_data["date"].split('T')[0]==datetime.today().strftime("%Y-%m-%d")):
                    df_company_news = pd.DataFrame(tmp_data["data"])
        timeZone = 'US/Pacific'
        headers = {'accept': 'application/json'}

        df_company_daily_news = self.getDaily2NewsForEvents(msig_data["df_market_capital_price"],
                                                       msig_data["indicators_price"], 'finL2Extension.graphml')
        mi_list = msig_data["events_price"]["main indicator"]
        ti_list = msig_data["events_price"]["trailing indicator"]
        li_list = msig_data["events_price"]["leading indicator"]
        count =0
        for mi in mi_list:

            li_dt = datetime.strptime(li_list[str(count)], "%Y-%m-%d %H:%M:%S")
            mi_dt = datetime.strptime(mi_list[mi], "%Y-%m-%d %H:%M:%S")
            ti_dt = datetime.strptime(ti_list[str(count)], "%Y-%m-%d %H:%M:%S")

            mi_ts = datetime.timestamp(mi_dt) *1000
            ti_ts =datetime.timestamp(ti_dt)*1000
            li_ts = datetime.timestamp(li_dt)*1000

            dict_e = {}
            dict_e["main indicator"] = mi_dt
            dict_e["trailing indicator"] = ti_dt
            dict_e["leading indicator"] = li_dt
            e = pd.Series(dict_e)

            eventDateTimeStampEpochs = int(mi_ts)
            tmp_date = str(datetime.fromtimestamp(eventDateTimeStampEpochs / 1000).astimezone(pytz.timezone(timeZone)))
            event_type = "price"
            category= "GAIN/LOSS"
            newsTitle = "A " + category + " event based on PRICE detected @ " + tmp_date[:tmp_date.rfind('-')]

            htmlStory = self.generateHtmlStory(msig_data, count, e, event_type, 60000,
                                          msig_data["ts_price_min"], timeZone, df_company_news, category,
                                          df_company_daily_news)
            indicators = []
            tmp = df_market_capital_price[df_market_capital_price["event_number"] == count + 1].sort_values(
                by="market_capital", ascending=False)
            for j, p in df_market_capital_price[df_market_capital_price["event_number"] == count + 1].iterrows():
                if (p["indicator_type"] == "leading indicator"):
                    eventRole = "Leading Indicator"
                elif (p["indicator_type"] == "main indicator"):
                    eventRole = "Main Indicator"
                else:
                    eventRole = "Trailing Indicator"
                indicators.append({"symbol": p["symbol"],
                                   "volume": p["volume"],
                                   "price": p["price"],
                                   "eventRole": eventRole})
            htmlData = [{"eventDateTimeStampEpochs": eventDateTimeStampEpochs,
                         "htmlData": htmlStory,
                         "newsTitle": newsTitle,
                         "indicators": indicators, "eventFlag": "Price",
                         'isGain': True}]
            response = requests.post(url, headers=headers, json=htmlData)
            count = count + 1

            if (response.text):
                print(response.text)

        mi_list = msig_data["events_volume"]["main indicator"]
        ti_list = msig_data["events_volume"]["trailing indicator"]
        li_list = msig_data["events_volume"]["leading indicator"]
        count = 0
        for mi in mi_list:

            li_dt = datetime.strptime(li_list[str(count)], "%Y-%m-%d %H:%M:%S")
            mi_dt = datetime.strptime(mi_list[mi], "%Y-%m-%d %H:%M:%S")
            ti_dt = datetime.strptime(ti_list[str(count)], "%Y-%m-%d %H:%M:%S")

            mi_ts = datetime.timestamp(mi_dt)*1000
            ti_ts = datetime.timestamp(ti_dt)*1000
            li_ts = datetime.timestamp(li_dt)*1000

            dict_e = {}
            dict_e["main indicator"] = mi_ts
            dict_e["trailing indicator"] = ti_ts
            dict_e["leading indicator"] = li_ts
            e = pd.Series(dict_e)
            eventDateTimeStampEpochs = int(mi_ts)

            tmp_date = str(datetime.fromtimestamp(eventDateTimeStampEpochs / 1000).astimezone(pytz.timezone(timeZone)))
            event_type = "volume"

            category= "GAIN/LOSS"
            isGain = True

            newsTitle = "A " + category + " event based on VOLUME detected @ " + tmp_date[:tmp_date.rfind('-')]
            htmlStory = self.generateHtmlStory(msig_data, count, e, event_type, 60000,
                                          msig_data["ts_volume_min"], timeZone, df_company_news, category)
            indicators = []
            tmp = df_market_capital_volume[df_market_capital_volume["event_number"] == count + 1].sort_values(
                by="market_capital", ascending=False)
            for j, p in df_market_capital_volume[df_market_capital_volume["event_number"] == count + 1].iterrows():
                if (p["indicator_type"] == "leading indicator"):
                    eventRole = "Leading Indicator"
                elif (p["indicator_type"] == "main indicator"):
                    eventRole = "Main Indicator"
                else:
                    eventRole = "Trailing Indicator"
                indicators.append({"symbol": p["symbol"],
                                   "volume": p["volume"],
                                   "price": p["price"],
                                   "eventRole": eventRole})
            htmlData = [{"eventDateTimeStampEpochs": eventDateTimeStampEpochs,
                         "htmlData": htmlStory,
                         "newsTitle": newsTitle,
                         "indicators": indicators, "eventFlag": "Volume",
                         'isGain': isGain}]

            response = requests.post(url, headers=headers, json=htmlData)
            count = count+1
            if (response.text):
                print(response.text)
        # post sector news
        # Tying sector news to the first main time stamp of the price events
        if (redis_msig.ping()):
            tmp_data = redis_msig.lpop("NewsIndustry")
            if tmp_data != None:
                redis_msig.lpush("NewsIndustry", tmp_data)
                if (len(tmp_data) > 0):
                    tmp_data = pickle.loads(tmp_data)
                    # if(tmp_data["date"].split('T')[0]==datetime.today().strftime("%Y-%m-%d")):
                    df_industry_news = pd.DataFrame(tmp_data["data"])
                    df_industry_news = df_industry_news.sort_values(by=["compound"], ascending=False)
                    df_industry_news = df_industry_news.drop_duplicates(subset=["newsLink"], keep="first")
                    if (len(df_industry_news) > 0):
                        eventDateTimeStampEpochs = msig_data["ts_price_min"]
                        tmp_date = str(
                            datetime.fromtimestamp(eventDateTimeStampEpochs / 1000).astimezone(pytz.timezone(timeZone)))
                        newsTitle = "Sector/Industry news and their MAGI Scores @ " + tmp_date[:tmp_date.rfind('-')]
                        htmlStory = ""
                        z = 1
                        for k, inews in df_industry_news.iterrows():
                            htmlStory = htmlStory + "<li><strong>" + inews["sector"] + "/" + inews[
                                "industry"] + " : </strong><a href=" + str(inews["newsLink"]) + ">" + str(
                                inews["newsTitle"]) + "</a> (MAGI Score=" + str(inews["compound"]) + ").</li>"
                            z = z + 1
                            if (z == 50): break
                        htmlData = [{"eventDateTimeStampEpochs": eventDateTimeStampEpochs,
                                     "htmlData": htmlStory,
                                     "newsTitle": newsTitle, "indicators": [], "eventFlag": "Price"}]
                        response = requests.post(url, headers=headers, json=htmlData)
                        if (response.text):
                            print(response.text)
        # CURATED NEWS
        curated_topics = ''.split(',')
        htmlStory = ""
        if (len(curated_topics) > 5):
            print(
                "More than 5 topics detected in cratedNews. This will overwhelm the News API. Using only the first 5 topics.")
            curated_topics = curated_topics[:5]
        if (len(curated_topics) > 0):
            curated_topics = [str.strip(x) for x in curated_topics]
            df_curated_news = self.getDailyCuratedNews(curated_topics)
            if (len(df_curated_news) > 0):
                eventDateTimeStampEpochs = msig_data["ts_price_min"] - 1001
                tmp_date = str(
                    datetime.fromtimestamp(eventDateTimeStampEpochs / 1000).astimezone(pytz.timezone(timeZone)))
                newsTitle = "Today's Top News & MAGI Scores"
                htmlStory = "<strong>Political" + " News:</strong><br>"
                for k, topnews in df_curated_news.iterrows():
                    if (k == 5 or k == 10):
                        htmlStory = htmlStory + "<br><strong>" + topnews[
                            "fullName"] + " News:</strong><br>" + "<li><strong>" + "</strong><a href=" + str(
                            topnews["newsLink"]) + ">" + str(topnews["newsTitle"]) + "</a> (MAGI Score=" + str(
                            topnews["compound"]) + ").</li>"
                    else:
                        htmlStory = htmlStory + "<li><strong>" + "</strong><a href=" + str(
                            topnews["newsLink"]) + ">" + str(topnews["newsTitle"]) + "</a> (MAGI Score=" + str(
                            topnews["compound"]) + ").</li>"
                htmlData = [{"eventDateTimeStampEpochs": eventDateTimeStampEpochs,
                             "htmlData": htmlStory,
                             "newsTitle": newsTitle, "indicators": [], "eventFlag": "Price"}]
                response = requests.post(url, headers=headers, json=htmlData)
                if (response.text):
                    print(response.text)
                    # END CURATED NEWS
    def sendNewsToFrontEnd_v2(self,msig_data,df_market_capital_price,df_market_capital_volume,url = 'http://localhost:5000/Events/PostEvents',num_events_price_gain=0,num_events_volume_gain=0,isStartofDay=False, curated_news_topics: str = "Politics,COVID-19,Bitcoin,Supply Chain Disruption 2021", is_historical=False, redis_port: int = 6379):
        import json
        import requests
        from datetime import datetime
        import pytz
        import redis
        import pandas as pd
        import pickle
        redis_msig = redis.Redis(host='localhost', port=redis_port)
        df_company_news=pd.DataFrame()
        df_company_daily_news=pd.DataFrame()
        df_curated_news=pd.DataFrame()
        if(redis_msig.ping()):
            tmp_data=redis_msig.lpop("NewsCompany")
            if tmp_data != None:
                redis_msig.lpush("NewsCompany", tmp_data)
                if (len(tmp_data) > 0):
                    tmp_data = pickle.loads(tmp_data)
                    # if(tmp_data["date"].split('T')[0]==datetime.today().strftime("%Y-%m-%d")):
                    df_company_news = pd.DataFrame(tmp_data["data"])
        timeZone = 'US/Pacific'
        headers = {'accept': 'application/json'}

        if not is_historical:
            df_company_daily_news=self.getDaily2NewsForEvents_v2(msig_data["df_market_capital_price"],msig_data["indicators_price"],'finL2Extension.graphml')
        else:
            df_company_daily_news = pd.DataFrame()

        for i,e in msig_data["events_price"].iterrows():
            x = datetime.strptime(e["main indicator"], "%Y-%m-%d %H:%M:%S")
            y = datetime.timestamp(x)  *1000
            eventDateTimeStampEpochs=y
            tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
            event_type="price"
            i = int(i)
            if(i<=num_events_price_gain):
                category="GAIN"
                isGain=True
            else:
                category="LOSS"
                isGain=False
            newsTitle="A "+category+ " event based on PRICE detected @ "+ tmp_date[:tmp_date.rfind('-')]
            #print(newsTitle)
            htmlStory=self.generateHtmlStory_v2(msig_data,i,e,event_type,60000,msig_data["ts_price_min"],timeZone,df_company_news,category,df_company_daily_news)
            indicators=[]
            tmp=df_market_capital_price[df_market_capital_price["event_number"]==i+1].sort_values(by="market_capital",ascending=False)
            for j,p in df_market_capital_price[df_market_capital_price["event_number"]==i+1].iterrows():
                if(p["indicator_type"]=="leading indicator"):eventRole="Leading Indicator"
                elif(p["indicator_type"]=="main indicator"):eventRole="Main Indicator"
                else:eventRole="Trailing Indicator"
                indicators.append( {"symbol": p["symbol"],
                                    "volume": p["volume"],
                                    "price":  p["price"],
                                    "eventRole": eventRole})
            htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                      "htmlData": htmlStory,
                      "newsTitle":newsTitle,
                      "indicators":indicators,"eventFlag":"Price",
                      'isGain':isGain}]
            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)

        for i,e in msig_data["events_volume"].iterrows():
            x = datetime.strptime(e["main indicator"], "%Y-%m-%d %H:%M:%S")
            y = datetime.timestamp(x) *1000
            eventDateTimeStampEpochs=y
            tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
            event_type="volume"
            i = int(i)
            if(i<=num_events_volume_gain):
                category="GAIN"
                isGain=True
            else:
                category="LOSS"
                isGain=False
            newsTitle="A "+category+ " event based on VOLUME detected @ "+ tmp_date[:tmp_date.rfind('-')]
            htmlStory=self.generateHtmlStory_v2(msig_data,i,e,event_type,60000,msig_data["ts_volume_min"],timeZone,df_company_news,category)
            indicators=[]
            tmp=df_market_capital_volume[df_market_capital_volume["event_number"]==i+1].sort_values(by="market_capital",ascending=False)
            for j,p in df_market_capital_volume[df_market_capital_volume["event_number"]==i+1].iterrows():
                if(p["indicator_type"]=="leading indicator"):eventRole="Leading Indicator"
                elif(p["indicator_type"]=="main indicator"):eventRole="Main Indicator"
                else:eventRole="Trailing Indicator"
                indicators.append( {"symbol": p["symbol"],
                                    "volume": p["volume"],
                                    "price":  p["price"],
                                    "eventRole": eventRole})
            htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                      "htmlData": htmlStory,
                      "newsTitle":newsTitle,
                      "indicators":indicators,"eventFlag":"Volume",
                      'isGain':isGain}]

            response = requests.post(url,headers=headers,json=htmlData)
            if(response.text):
                print(response.text)
        #post sector news
        #Tying sector news to the first main time stamp of the price events
        if(redis_msig.ping()):
            tmp_data=redis_msig.lpop("NewsIndustry")
            if tmp_data != None:
                redis_msig.lpush("NewsIndustry", tmp_data)
                if(len(tmp_data)>0):
                    tmp_data=pickle.loads(tmp_data)
                #if(tmp_data["date"].split('T')[0]==datetime.today().strftime("%Y-%m-%d")):
                    df_industry_news=pd.DataFrame(tmp_data["data"])
                    df_industry_news=df_industry_news.sort_values(by=["compound"],ascending=False)
                    df_industry_news=df_industry_news.drop_duplicates(subset=["newsLink"],keep="first")
                    if(len(df_industry_news)>0):
                        eventDateTimeStampEpochs=msig_data["ts_price_min"]
                        tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
                        newsTitle="Sector/Industry news and their MAGI Scores @ "+ tmp_date[:tmp_date.rfind('-')]
                        htmlStory=""
                        z=1
                        for k,inews in df_industry_news.iterrows():
                            htmlStory=htmlStory+"<li><strong>"+inews["sector"] + "/" if not is_historical else "" + inews["industry"] + ":" if not is_historical else "" +" </strong><a href="+str(inews["newsLink"])+">"+str(inews["newsTitle"])+"</a> (MAGI Score="+str(inews["compound"])+").</li>"
                            z=z+1
                            if(z==50):break
                        htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                          "htmlData": htmlStory,
                          "newsTitle":newsTitle,"indicators":[],"eventFlag":"Price"}]
                        response = requests.post(url,headers=headers,json=htmlData)
                        if(response.text):
                            print(response.text)
        #CURATED NEWS
        curated_topics = curated_news_topics.split(',')
        htmlStory=""
        if(len(curated_topics)>5):
            print("More than 5 topics detected in cratedNews. This will overwhelm the News API. Using only the first 5 topics.")
            curated_topics=curated_topics[:5]
        if(len(curated_topics)>1):
            curated_topics=[str.strip(x) for x in curated_topics]
            if not is_historical:
                df_curated_news=self.getDailyCuratedNews(curated_topics)
            else:
                df_curated_news = pd.DataFrame()
            if(len(df_curated_news)>0):
              eventDateTimeStampEpochs=msig_data["ts_price_min"]-1001
              tmp_date=str(datetime.fromtimestamp(eventDateTimeStampEpochs/1000).astimezone(pytz.timezone(timeZone)))
              newsTitle="Today's Top News & MAGI Scores"
              htmlStory="<strong>Political"+ " News:</strong><br>"
              for k,topnews in df_curated_news.iterrows():
                  if(k % 5 == 0):
                      htmlStory=htmlStory+"<br><strong>"+topnews["fullName"]+" News:</strong><br>"+"<li><strong>"+"</strong><a href="+str(topnews["newsLink"])+">"+str(topnews["newsTitle"])+"</a> (MAGI Score="+str(topnews["compound"])+").</li>"
                  else:
                      htmlStory=htmlStory+"<li><strong>"+"</strong><a href="+str(topnews["newsLink"])+">"+str(topnews["newsTitle"])+"</a> (MAGI Score="+str(topnews["compound"])+").</li>"
              htmlData=[{ "eventDateTimeStampEpochs":eventDateTimeStampEpochs,
                      "htmlData": htmlStory,
                      "newsTitle":newsTitle,"indicators":[],"eventFlag":"Price"}]
              response = requests.post(url,headers=headers,json=htmlData)
              if(response.text):
                  print(response.text)
        #END CURATED NEWS
    def generateHtmlStory(self,msig_data, i, e, event_type, bucket_size_msec=60000, min_ts=int(time.time() * 1000),
                          timeZone='US/Pacific', df_company_news=None, category="GAIN",
                          df_company_daily_news=pd.DataFrame()):
        from datetime import datetime
        import pytz
        import pandas as pd
        import numpy as np
        market_cap = 0
        start_time = "could not be detectected"
        end_time = "could not be detected"
        main_time = "could not be detected"

        start_time = e["leading indicator"]
        end_time = e["trailing indicator"]
        main_time = e["main indicator"]

        sectors = "could not be detected"
        industries = "could not be detected"
        companies_table = "<br>"
        news_snippet = "<br>"
        df_company_news["prefix"] = ""
        if (len(df_company_daily_news) > 0):
            df_company_news = df_company_news.append(df_company_daily_news, ignore_index=True)
        if (event_type == 'price'):
            tmp = list(msig_data["df_sectors_price"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                sectors = ', '.join(list(set(tmp)))

            tmp = list(msig_data["df_industries_price"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                industries = ', '.join(list(set(tmp)))

            tmp = msig_data["df_market_capital_price"][msig_data["df_market_capital_price"]["event_number"] == i + 1][
                "market_capital"].values
            if (len(tmp) > 0):
                market_cap = "$" + str(round(sum(tmp), 2))

            if (type(e["leading indicator"]) == int):
                eventDateTimeStampEpochs = e["leading indicator"]
                tmp = int(e["leading indicator"] )
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                start_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["main indicator"]) == int):
                eventDateTimeStampEpochs = e["main indicator"]
                tmp = int((e["main indicator"] ))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                main_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["trailing indicator"]) == int):
                eventDateTimeStampEpochs = e["trailing indicator"]
                tmp = int((e["trailing indicator"] ))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                end_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            tmp = pd.DataFrame(msig_data["df_market_capital_price"][
                                   msig_data["df_market_capital_price"]["event_number"] == i + 1].sort_values(
                by=["market_capital"], ascending=False))
            tmp = tmp.astype({'volume': 'int32'})
            if (len(df_company_news) > 0):
                df_event_news = df_company_news[df_company_news["symbol"].isin(list(tmp["symbol"].values))].sort_values(
                    by=["compound"], ascending=False)
                if (category == "GAIN"):
                    df_event_news = df_event_news[df_event_news["compound"] > 0.05]
                    df_event_news["max_compound"] = df_event_news.groupby("symbol")["compound"].transform('max')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["max_compound"]].drop(
                        ["max_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="first")
                else:
                    df_event_news = df_event_news[df_event_news["compound"] < 0]
                    df_event_news["min_compound"] = df_event_news.groupby("symbol")["compound"].transform('min')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["min_compound"]].drop(
                        ["min_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="last")
                if (len(df_event_news) > 0):
                    news_snippet = "<br> MAGI has found the following news and analyzed them between -1 and 1 related to this event:"
                    for j, n in df_event_news.iterrows():
                        news_snippet = news_snippet + "<li><em>" + str(n["prefix"]) + "</em><a href=" + str(
                            n["newsLink"]) + ">" + str(n["newsTitle"]) + "</a> (MAGI Score=" + str(
                            n["compound"]) + ").</li>"
                        if (j == 50): break
                    news_snippet = news_snippet + "<br>"
            companies_table = tmp.to_html(index=False, header=True,
                                          columns=['symbol', 'price', 'volume', 'market_capital', 'indicator_type'],
                                          justify='center', na_rep='Unknown', float_format='%10.2f USD')
            companies_table = companies_table.replace('symbol', 'Symbol')
            companies_table = companies_table.replace('price', 'Price')
            companies_table = companies_table.replace('volume', 'Volume')
            companies_table = companies_table.replace('market_capital', 'Market Capital')
            companies_table = companies_table.replace('indicator_type', 'Role')
        else:  # volume
            tmp = list(msig_data["df_sectors_volume"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                sectors = ', '.join(list(set(tmp)))

            tmp = list(msig_data["df_industries_volume"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                industries = ', '.join(list(set(tmp)))

            tmp = msig_data["df_market_capital_volume"][msig_data["df_market_capital_volume"]["event_number"] == i + 1][
                "market_capital"].values
            if (len(tmp) > 0):
                market_cap = "$" + str(round(sum(tmp), 2))

            if (type(e["leading indicator"]) == int):
                eventDateTimeStampEpochs = e["leading indicator"]
                tmp = int((e["leading indicator"] ))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                start_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["main indicator"]) == int):
                eventDateTimeStampEpochs = e["main indicator"]
                tmp = int((e["main indicator"] ))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                main_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["trailing indicator"]) == int):
                eventDateTimeStampEpochs = e["trailing indicator"]
                tmp = int((e["trailing indicator"] ))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                end_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            tmp = pd.DataFrame(msig_data["df_market_capital_volume"][
                                   msig_data["df_market_capital_volume"]["event_number"] == i + 1].sort_values(
                by=["market_capital"], ascending=False))
            tmp = tmp.astype({'volume': 'int32'})
            if (len(df_company_news) > 0):
                df_event_news = df_company_news[df_company_news["symbol"].isin(list(tmp["symbol"].values))].sort_values(
                    by=["compound"], ascending=False)
                if (category == "GAIN"):
                    df_event_news = df_event_news[df_event_news["compound"] > 0.05]
                    df_event_news["max_compound"] = df_event_news.groupby("symbol")["compound"].transform('max')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["max_compound"]].drop(
                        ["max_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="first")
                else:
                    df_event_news = df_event_news[df_event_news["compound"] < 0]
                    df_event_news["min_compound"] = df_event_news.groupby("symbol")["compound"].transform('min')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["min_compound"]].drop(
                        ["min_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="last")
                if (len(df_event_news) > 0):
                    news_snippet = "<br> MAGI has found the following news and analyzed them between -1 and 1 related to this event:"
                    for j, n in df_event_news.iterrows():
                        news_snippet = news_snippet + "<li><em>" + str(n["prefix"]) + "</em><a href=" + str(
                            n["newsLink"]) + ">" + str(n["newsTitle"]) + "</a> (MAGI Score=" + str(
                            n["compound"]) + ").</li>"
                        if (j == 50): break
                    news_snippet = news_snippet + "<br>"

            companies_table = tmp.to_html(index=False, header=True,
                                          columns=['symbol', 'price', 'volume', 'market_capital', 'indicator_type'],
                                          justify='center', na_rep='Unknown', float_format='%10.2f USD')
            companies_table = companies_table.replace('symbol', 'Symbol')
            companies_table = companies_table.replace('price', 'Price')
            companies_table = companies_table.replace('volume', 'Volume')
            companies_table = companies_table.replace('market_capital', 'Market Capital')
            companies_table = companies_table.replace('indicator_type', 'Role')
        template = "<h3>Here are the details:</h3> \
                    <br> \
                    <p>MagiFinance detected an event of size <strong>" + str(market_cap) + ".</strong>\
                    The event seems to affect the <strong>sectors</strong>= <em>" + str(sectors) + "</em>, \
                    and the corresponding <strong>industries</strong>=<em>" + str(industries) + ".</em><br>\
                    The timing of the event is as follows:\
                    <li>Starting time of the event @ <strong>" + str(start_time) + "</strong></li>\n \
                    <li>Main/peak time of the event @ <strong>" + str(main_time) + "</strong></li>\n \
                    <li>Trailing time of the event @ <strong>" + str(end_time) + "</strong></li><br>\
                    Please scroll down for related <strong>news</strong> and a <strong>summary table</strong>.\n <br>" + str(
            news_snippet) + str(companies_table)
        return template

    def generateHtmlStory_v2(self,msig_data, i, e, event_type, bucket_size_msec=60000, min_ts=int(time.time() * 1000),
                          timeZone='US/Pacific', df_company_news=None, category="GAIN",
                          df_company_daily_news=pd.DataFrame()):
        from datetime import datetime
        import pytz
        import pandas as pd
        market_cap = 0
        start_time = "could not be detectected"
        end_time = "could not be detected"
        main_time = "could not be detected"

        start_time = e["leading indicator"]
        end_time = e["trailing indicator"]
        main_time = e["main indicator"]

        sectors = "could not be detected"
        industries = "could not be detected"
        companies_table = "<br>"
        news_snippet = "<br>"
        df_company_news["prefix"] = ""
        if (len(df_company_daily_news) > 0):
            df_company_news = df_company_news.append(df_company_daily_news, ignore_index=True)
        if (event_type == 'price'):
            tmp = list(msig_data["df_sectors_price"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                sectors = ', '.join(list(set(tmp)))

            tmp = list(msig_data["df_industries_price"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                industries = ', '.join(list(set(tmp)))

            tmp = msig_data["df_market_capital_price"][msig_data["df_market_capital_price"]["event_number"] == i + 1][
                "market_capital"].values
            if (len(tmp) > 0):
                market_cap = "$" + str(round(sum(tmp), 2))

            if (type(e["leading indicator"]) == int):
                eventDateTimeStampEpochs = e["leading indicator"]
                tmp = int((e["leading indicator"] * bucket_size_msec + min_ts))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                start_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["main indicator"]) == int):
                eventDateTimeStampEpochs = e["main indicator"]
                tmp = int((e["main indicator"] * bucket_size_msec + min_ts))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                main_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["trailing indicator"]) == int):
                eventDateTimeStampEpochs = e["trailing indicator"]
                tmp = int((e["trailing indicator"] * bucket_size_msec + min_ts))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                end_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            tmp = pd.DataFrame(msig_data["df_market_capital_price"][
                                   msig_data["df_market_capital_price"]["event_number"] == i + 1].sort_values(
                by=["market_capital"], ascending=False))
            tmp = tmp.astype({'volume': 'int32'})
            if (len(df_company_news) > 0):
                df_event_news = df_company_news[df_company_news["symbol"].isin(list(tmp["symbol"].values))].sort_values(
                    by=["compound"], ascending=False)
                if (category == "GAIN"):
                    df_event_news = df_event_news[df_event_news["compound"] > 0.05]
                    df_event_news["max_compound"] = df_event_news.groupby("symbol")["compound"].transform('max')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["max_compound"]].drop(
                        ["max_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="first")
                else:
                    df_event_news = df_event_news[df_event_news["compound"] < 0]
                    df_event_news["min_compound"] = df_event_news.groupby("symbol")["compound"].transform('min')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["min_compound"]].drop(
                        ["min_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="last")
                if (len(df_event_news) > 0):
                    news_snippet = "<br> MAGI has found the following news and analyzed them between -1 and 1 related to this event:"
                    for j, n in df_event_news.iterrows():
                        news_snippet = news_snippet + "<li><em>" + str(n["prefix"]) + f"Published: {n['date_published']} " +"</em><a href=" + str(
                            n["newsLink"]) + ">" + str(n["newsTitle"]) + "</a> (MAGI Score=" + str(
                            n["compound"]) + ").</li>"
                        if (j == 50): break
                    news_snippet = news_snippet + "<br>"
            companies_table = tmp.to_html(index=False, header=True,
                                          columns=['symbol', 'price', 'volume', 'market_capital', 'indicator_type'],
                                          justify='center', na_rep='Unknown', float_format='%10.2f USD')
            companies_table = companies_table.replace('symbol', 'Symbol')
            companies_table = companies_table.replace('price', 'Price')
            companies_table = companies_table.replace('volume', 'Volume')
            companies_table = companies_table.replace('market_capital', 'Market Capital')
            companies_table = companies_table.replace('indicator_type', 'Role')
        else:  # volume
            tmp = list(msig_data["df_sectors_volume"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                sectors = ', '.join(list(set(tmp)))

            tmp = list(msig_data["df_industries_volume"].iloc[i, :].values)
            tmp = sum(tmp, [])
            if (len(tmp) > 0):
                industries = ', '.join(list(set(tmp)))

            tmp = msig_data["df_market_capital_volume"][msig_data["df_market_capital_volume"]["event_number"] == i + 1][
                "market_capital"].values
            if (len(tmp) > 0):
                market_cap = "$" + str(round(sum(tmp), 2))

            if (type(e["leading indicator"]) == int):
                eventDateTimeStampEpochs = e["leading indicator"]
                tmp = int((e["leading indicator"] * bucket_size_msec + min_ts))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                start_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["main indicator"]) == int):
                eventDateTimeStampEpochs = e["main indicator"]
                tmp = int((e["main indicator"] * bucket_size_msec + min_ts))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                main_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            if (type(e["trailing indicator"]) == int):
                eventDateTimeStampEpochs = e["trailing indicator"]
                tmp = int((e["trailing indicator"] * bucket_size_msec + min_ts))
                tmp = str(datetime.fromtimestamp(tmp / 1000).astimezone(pytz.timezone(timeZone)))
                end_time = tmp[tmp.find(' ') + 1:tmp.rfind('-')]

            tmp = pd.DataFrame(msig_data["df_market_capital_volume"][
                                   msig_data["df_market_capital_volume"]["event_number"] == i + 1].sort_values(
                by=["market_capital"], ascending=False))
            tmp = tmp.astype({'volume': 'int32'})
            if (len(df_company_news) > 0):
                df_event_news = df_company_news[df_company_news["symbol"].isin(list(tmp["symbol"].values))].sort_values(
                    by=["compound"], ascending=False)
                if (category == "GAIN"):
                    df_event_news = df_event_news[df_event_news["compound"] > 0.05]
                    df_event_news["max_compound"] = df_event_news.groupby("symbol")["compound"].transform('max')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["max_compound"]].drop(
                        ["max_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="first")
                else:
                    df_event_news = df_event_news[df_event_news["compound"] < 0]
                    df_event_news["min_compound"] = df_event_news.groupby("symbol")["compound"].transform('min')
                    df_event_news = df_event_news[df_event_news["compound"] == df_event_news["min_compound"]].drop(
                        ["min_compound"], axis=1)
                    df_event_news = df_event_news.drop_duplicates(subset=["newsTitle"], keep="last")
                if (len(df_event_news) > 0):
                    news_snippet = "<br> MAGI has found the following news and analyzed them between -1 and 1 related to this event:"
                    for j, n in df_event_news.iterrows():
                        news_snippet = news_snippet + "<li><em>" + str(n["prefix"]) + "</em><a href=" + str(
                            n["newsLink"]) + ">" + str(n["newsTitle"]) + "</a> (MAGI Score=" + str(
                            n["compound"]) + ").</li>"
                        if (j == 50): break
                    news_snippet = news_snippet + "<br>"

            companies_table = tmp.to_html(index=False, header=True,
                                          columns=['symbol', 'price', 'volume', 'market_capital', 'indicator_type'],
                                          justify='center', na_rep='Unknown', float_format='%10.2f USD')
            companies_table = companies_table.replace('symbol', 'Symbol')
            companies_table = companies_table.replace('price', 'Price')
            companies_table = companies_table.replace('volume', 'Volume')
            companies_table = companies_table.replace('market_capital', 'Market Capital')
            companies_table = companies_table.replace('indicator_type', 'Role')
        template = "<h3>Here are the details:</h3> \
                    <br> \
                    <p>MagiFinance detected an event of size <strong>" + str(market_cap) + ".</strong>\
                    The event seems to affect the <strong>sectors</strong>= <em>" + str(sectors) + "</em>, \
                    and the corresponding <strong>industries</strong>=<em>" + str(industries) + ".</em><br>\
                    The timing of the event is as follows:\
                    <li>Starting time of the event @ <strong>" + str(start_time) + "</strong></li>\n \
                    <li>Main/peak time of the event @ <strong>" + str(main_time) + "</strong></li>\n \
                    <li>Trailing time of the event @ <strong>" + str(end_time) + "</strong></li><br>\
                    Please scroll down for related <strong>news</strong> and a <strong>summary table</strong>.\n <br>" + str(
            news_snippet) + str(companies_table)
        return template
    def getDailyCuratedNews(self,curated_topics):
        import pandas as pd
        df_curated_news = pd.DataFrame()
        import time
        from datetime import datetime, timedelta
        print("Checking curated news topics...")
        start = time.time()
        x = datetime.today()
        todays_start_date_for_news = (datetime(x.year, x.month, x.day, 00, 1)).strftime('%Y-%m-%dT%H:%M:%S')
        todays_end_date_for_news = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
        for topic in curated_topics:
            df_tmp = self.analyzeNewsUsingRapidAPI(topic, "top news", todays_start_date_for_news, todays_end_date_for_news,
                                              page_size=5, category=" ")
            if (len(df_tmp) > 0):
                df_curated_news = df_curated_news.append(df_tmp, ignore_index=True)
        print(time.time() - start, "sec. to analyze curated news. Sending them to the front end...")
        return df_curated_news

    def getDaily2NewsForEvents(self,df_market_capital_price, indicators_price, todays_start_date_for_news=None,
                               todays_end_date_for_news=None, L2fileName="finL2Extension.graphml"):
        import pandas as pd
        import networkx as nx
        import time
        from datetime import datetime, timedelta
        print("Checking business-hour news for")
        start = time.time()
        companies = []
        G = nx.read_graphml(L2fileName)
        all_nodes = pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index')
        df_companies_summary = pd.DataFrame(all_nodes[["symbol", "fullName"]])

        df_companies_sorted = pd.DataFrame(df_market_capital_price)
        _ = df_companies_sorted.sort_values(by=['event_number', 'market_capital'], ascending=False).groupby(
            'event_number')
        num_events = max(df_companies_sorted['event_number'].values)
        # ADD largest market caps
        for i in range(1, num_events + 1):
            df_tmp = df_companies_sorted[df_companies_sorted['event_number'] == i].sort_values(by=["market_capital"],
                                                                                               ascending=False)
            for j, r in df_tmp.iterrows():
                if (r["symbol"].strip() not in companies):
                    companies.append(r["symbol"].strip())
                    break
        # ADD top indicators (highest percent change)
        for mi in indicators_price["main indicator"]:
            for m in mi:
                list = indicators_price["main indicator"][m]
                for i in list:
                    m_company=i.split(':')[3]
                    if (m_company.strip() not in companies):
                        companies.append(m_company.strip())
                        break
        if (len(companies) > 0):
            print(companies)
            df_companies_summary = df_companies_summary.loc[df_companies_summary['symbol'].isin(companies)]
            if (todays_start_date_for_news == None):
                x = datetime.today()
                todays_start_date_for_news = (datetime(x.year, x.month, x.day, 13, 00) - timedelta(days=1)).strftime(
                    '%Y-%m-%dT%H:%M:%S')
            if (todays_end_date_for_news == None):
                todays_end_date_for_news = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
            df_company_daily_news = pd.DataFrame()
            for i, r in df_companies_summary.iterrows():
                q = r["fullName"].strip()
                df_tmp = self.analyzeNewsUsingRapidAPI(q, r["symbol"].strip(), todays_start_date_for_news,
                                                  todays_end_date_for_news, page_size=5, category=" ")
                if (len(df_tmp) > 0):
                    df_company_daily_news = df_company_daily_news.append(df_tmp, ignore_index=True)
        print("Number of daily news found=", len(df_company_daily_news))
        print("Finished analysing daily news in", time.time() - start, "sec")
        df_company_daily_news["prefix"] = "(NEW) "
        return df_company_daily_news

    def getDaily2NewsForEvents_v2(self,df_market_capital_price, indicators_price, todays_start_date_for_news=None,
                               todays_end_date_for_news=None, L2fileName="finL2Extension.graphml"):
        import pandas as pd
        import networkx as nx
        import time
        from datetime import datetime, timedelta
        print("Checking business-hour news for")
        start = time.time()
        companies = []
        G = nx.read_graphml(L2fileName)
        all_nodes = pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index')
        df_companies_summary = pd.DataFrame(all_nodes[["symbol", "fullName"]])

        df_companies_sorted = pd.DataFrame(df_market_capital_price)
        _ = df_companies_sorted.sort_values(by=['event_number', 'market_capital'], ascending=False).groupby(
            'event_number')
        num_events = max(df_companies_sorted['event_number'].values)
        # ADD largest market caps
        for i in range(1, num_events + 1):
            df_tmp = df_companies_sorted[df_companies_sorted['event_number'] == i].sort_values(by=["market_capital"],
                                                                                               ascending=False)
            for j, r in df_tmp.iterrows():
                if (r["symbol"].strip() not in companies):
                    companies.append(r["symbol"].strip())
                    break
        # ADD top indicators (highest percent change)
        for mi in indicators_price["main indicator"]:
            for m in mi:
                m = m.split(':')[3]
                if (m.strip() not in companies):
                    companies.append(m.strip())
                    break
        if (len(companies) > 0):
            print(companies)
            df_companies_summary = df_companies_summary.loc[df_companies_summary['symbol'].isin(companies)]
            if (todays_start_date_for_news == None):
                x = datetime.today()
                todays_start_date_for_news = (datetime(x.year, x.month, x.day, 13, 00) - timedelta(days=1)).strftime(
                    '%Y-%m-%dT%H:%M:%S')
            if (todays_end_date_for_news == None):
                todays_end_date_for_news = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
            df_company_daily_news = pd.DataFrame()
            for i, r in df_companies_summary.iterrows():
                q = r["fullName"].strip()
                df_tmp = self.analyzeNewsUsingRapidAPI(q, r["symbol"].strip(), todays_start_date_for_news,
                                                  todays_end_date_for_news, page_size=5, category=" ")
            if (len(df_tmp) > 0):
                df_company_daily_news = df_company_daily_news.append(df_tmp, ignore_index=True)
        print("Number of daily news found=", len(df_company_daily_news))
        print("Finished analysing daily news in", time.time() - start, "sec")
        df_company_daily_news["prefix"] = "(NEW) "
        return df_company_daily_news

    def analyzeNewsUsingRapidAPI(self,q:str,symbol,todays_start_date_for_news,todays_end_date_for_news,page_size=10,api_key="b8f7350d71msh5fb4b8934a2c3ffp1392c8jsne8a693abbebb",api_host="contextualwebsearch-websearch-v1.p.rapidapi.com",category='company financial'):
        import pandas as pd
        import requests
        import json
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

                news_str = self.preprocess_doc(news_data)
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
                        "date_published":date_published
                    })
        df_result=pd.DataFrame(ticker_financial_status_data)
        return df_result

    def preprocess_doc(self,single_doc):
        import nltk
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