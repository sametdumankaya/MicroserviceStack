import json
from datetime import datetime


class MetamodelUtils:
    def __init__(self, redis_output_client, neo4j_api_client):
        self.redis_output_client = redis_output_client
        self.neo4j_api_client = neo4j_api_client

    def create_metamodel_with_ts_output(self, output_name: str):
        data = self.redis_output_client.xrevrange(output_name, count=1)
        if data is None or len(data) == 0:
            return "No output data available."

        # Since only the last element is queried with xrevrange above, we can process the 0th element
        output_data_dict = json.loads(data[0][1]["data"])
        loop_no = output_data_dict["metadata"]["loop_no"]
        time_series_node_id = self.neo4j_api_client.find_node_id("Time Series", "L2.3")

        # Create initial nodes if not exist, then get their ids to construct graph for time series output
        if time_series_node_id is None:
            time_series_node_id = self.neo4j_api_client.create_node("Time Series", "L2.3")
            event_node_id = self.neo4j_api_client.create_node("Event", "L2.2")
            indicator_node_id = self.neo4j_api_client.create_node("Indicator", "L2.2")
            classified_event_node_id = self.neo4j_api_client.create_node("Classified Event", "L2.1")
            unclassified_event_node_id = self.neo4j_api_client.create_node("Unclassified Event", "L2.1")
            analyzed_node_id = self.neo4j_api_client.create_node("Analyzed", "L2.0")
            metadata_node_id = self.neo4j_api_client.create_node("Metadata", "L2.0")
            regime_node_id = self.neo4j_api_client.create_node("Regime", "L2.0")
            li_node_id = self.neo4j_api_client.create_node("Li", "L2.0")
            mi_node_id = self.neo4j_api_client.create_node("Mi", "L2.0")
            ti_node_id = self.neo4j_api_client.create_node("Ti", "L2.0")
            square_wave_node_id = self.neo4j_api_client.create_node("Square Wave", "L2.0")
            spike_node_id = self.neo4j_api_client.create_node("Spike", "L2.0")
            line_node_id = self.neo4j_api_client.create_node("Line", "L2.0")
            self.neo4j_api_client.add_intension(event_node_id, time_series_node_id)
            self.neo4j_api_client.add_antisymmetric_relation(event_node_id, indicator_node_id, "has")
            self.neo4j_api_client.add_intension(classified_event_node_id, event_node_id)
            self.neo4j_api_client.add_intension(unclassified_event_node_id, event_node_id)
            self.neo4j_api_client.add_intension(analyzed_node_id, time_series_node_id)
            self.neo4j_api_client.add_antisymmetric_relation(analyzed_node_id, metadata_node_id, "has")
            self.neo4j_api_client.add_antisymmetric_relation(analyzed_node_id, regime_node_id, "has")
            self.neo4j_api_client.add_intension(li_node_id, indicator_node_id)
            self.neo4j_api_client.add_intension(mi_node_id, indicator_node_id)
            self.neo4j_api_client.add_intension(ti_node_id, indicator_node_id)
            self.neo4j_api_client.add_intension(square_wave_node_id, time_series_node_id)
            self.neo4j_api_client.add_intension(spike_node_id, time_series_node_id)
            self.neo4j_api_client.add_intension(line_node_id, time_series_node_id)
        else:
            unclassified_event_node_id = self.neo4j_api_client.find_node_id("Unclassified Event", "L2.1")
            analyzed_node_id = self.neo4j_api_client.find_node_id("Analyzed", "L2.0")
            metadata_node_id = self.neo4j_api_client.find_node_id("Metadata", "L2.0")
            regime_node_id = self.neo4j_api_client.find_node_id("Regime", "L2.0")
            li_node_id = self.neo4j_api_client.find_node_id("Li", "L2.0")
            mi_node_id = self.neo4j_api_client.find_node_id("Mi", "L2.0")
            ti_node_id = self.neo4j_api_client.find_node_id("Ti", "L2.0")
            square_wave_node_id = self.neo4j_api_client.find_node_id("Square Wave", "L2.0")
            spike_node_id = self.neo4j_api_client.find_node_id("Spike", "L2.0")
            line_node_id = self.neo4j_api_client.find_node_id("Line", "L2.0")

        # line ts
        for line_ts in output_data_dict["Line"]:
            line_ts_node_id = self.neo4j_api_client.create_node(line_ts, "L1")
            self.neo4j_api_client.add_intension(line_ts_node_id, line_node_id)

        # spike ts
        for spike_ts in output_data_dict["Spike"]:
            spike_ts_node_id = self.neo4j_api_client.create_node(spike_ts, "L1")
            self.neo4j_api_client.add_intension(spike_ts_node_id, spike_node_id)

        # square ts
        for square_ts in output_data_dict["Square"]:
            square_ts_node_id = self.neo4j_api_client.create_node(square_ts, "L1")
            self.neo4j_api_client.add_intension(square_ts_node_id, square_wave_node_id)

        # analysis parameters
        metadata_dict = output_data_dict["metadata"]["parameters"]
        metadata_dict["start_ts"] = output_data_dict["metadata"]["start_ts"]
        metadata_dict["end_ts"] = output_data_dict["metadata"]["end_ts"]
        metadata_dict["min_ts"] = output_data_dict["metadata"]["min_ts"]
        metadata_dict["max_ts"] = output_data_dict["metadata"]["max_ts"]
        params_node_id = self.neo4j_api_client.create_node("params", "L1", metadata_dict)
        self.neo4j_api_client.add_intension(params_node_id, metadata_node_id)

        # analyzed together with regimes
        for idx, analyze in enumerate(output_data_dict["Analyzed"]):
            current_analyzed_node_id = self.neo4j_api_client.create_node(analyze, "L1")
            self.neo4j_api_client.add_intension(current_analyzed_node_id, analyzed_node_id)
            millisecond_regimes = output_data_dict["all_regimes"][idx]
            current_regime_node_id = self.neo4j_api_client.create_node(f"Regime{loop_no}_{idx + 1}", "L1", {
                "regime": ",".join([str(x) for x in millisecond_regimes])
            })
            self.neo4j_api_client.add_intension(current_regime_node_id, regime_node_id)
            self.neo4j_api_client.add_antisymmetric_relation(current_analyzed_node_id, current_regime_node_id, "has")

        # events
        for idx in range(len(output_data_dict["indicators"]["leading indicator"])):
            current_event_node_id = self.neo4j_api_client.create_node(f"Event{loop_no}_{idx + 1}", "L1")
            self.neo4j_api_client.add_intension(current_event_node_id, unclassified_event_node_id)
            event_leading_indicator_list = output_data_dict["indicators"]["leading indicator"][str(idx)]
            event_main_indicator_list = output_data_dict["indicators"]["main indicator"][str(idx)]
            event_trailing_indicator_list = output_data_dict["indicators"]["trailing indicator"][str(idx)]

            for leading_indicator in event_leading_indicator_list:
                current_leading_indicator_id = self.neo4j_api_client.find_node_id(leading_indicator, "L1")
                self.neo4j_api_client.add_intension(current_leading_indicator_id, li_node_id)
                self.neo4j_api_client.add_antisymmetric_relation(current_event_node_id, current_leading_indicator_id,
                                                                 "has")

            for main_indicator in event_main_indicator_list:
                current_main_indicator_id = self.neo4j_api_client.find_node_id(main_indicator, "L1")
                self.neo4j_api_client.add_intension(current_main_indicator_id, mi_node_id)
                self.neo4j_api_client.add_antisymmetric_relation(current_event_node_id, current_main_indicator_id,
                                                                 "has")

            for trailing_indicator in event_trailing_indicator_list:
                current_trailing_indicator_id = self.neo4j_api_client.find_node_id(trailing_indicator, "L1")
                self.neo4j_api_client.add_intension(current_trailing_indicator_id, ti_node_id)
                self.neo4j_api_client.add_antisymmetric_relation(current_event_node_id, current_trailing_indicator_id,
                                                                 "has")

        # contributors
        for key in output_data_dict["contributors"]["event"]:
            value = output_data_dict["contributors"]["event"][key]
            if value != "no_event":
                # create contributions
                contributor_name = output_data_dict["contributors"]["indicator"][key]
                contribution_amount = output_data_dict["contributors"]["contribution"][key]
                contributor_ts_node_id = self.neo4j_api_client.find_node_id(contributor_name, "L1")
                contribution_node_id = self.neo4j_api_client.create_node(f"{contributor_name}:Event{loop_no}_{value}",
                                                                         "L1")
                self.neo4j_api_client.add_antisymmetric_relation(contributor_ts_node_id, contribution_node_id,
                                                                 "contributes")

                # create follows temporally relations
                contributed_event_node_id = self.neo4j_api_client.find_node_id(f"Event{loop_no}_{value}", "L1")
                how_long = ""

                if output_data_dict["events"]["leading indicator"][str(value)] is not None or \
                        output_data_dict["events"]["leading indicator"][str(value)] != "Unknown":
                    d1 = datetime.strptime(output_data_dict["events"]["leading indicator"][str(value)],
                                           '%Y-%m-%d %H:%M:%S')
                    d2 = datetime.strptime(output_data_dict["events"]["main indicator"][str(value)],
                                           '%Y-%m-%d %H:%M:%S')
                    how_long = (d2 - d1).total_seconds() * 1000
                self.neo4j_api_client.follows_temporally(contributed_event_node_id, contributor_ts_node_id, how_many=1,
                                                         how_long=f"{str(how_long)} ms",
                                                         contribution_amount=contribution_amount)

        return True

    def create_metamodel_json_for_neo4j_nx(self, redis_name: str):
        data = self.redis_output_client.xrevrange(redis_name, count=1)
        if data is None or len(data) == 0:
            return "No output data available."

        # Since only the last element is queried with xrevrange above, we can process the 0th element
        output_data_dict = json.loads(data[0][1]["data"])
        loop_no = output_data_dict["metadata"]["loop_no"]

        json_for_neo4j = {"nodes": [], "relation_triplets": []}

        index = 0
        json_for_neo4j["nodes"].append(
            {'name': "Time Series", 'index': index, 'level': "L2.3", 'properties': {}})
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

        json_for_neo4j["nodes"].append(
            {'name': "Unclassified Event", 'index': index, 'level': "L2.1", 'properties': {}})
        unclassified_event_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Classified Event", 'index': index, 'level': "L2.1", 'properties': {}})
        classified_event_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Analyzed", 'index': index, 'level': "L2.0", 'properties': {}})
        analyzed_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Metadata", 'index': index, 'level': "L2.0", 'properties': {}})
        metadata_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Regime", 'index': index, 'level': "L2.0", 'properties': {}})
        regime_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Li", 'index': index, 'level': "L2.0", 'properties': {}})
        li_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Ti", 'index': index, 'level': "L2.0", 'properties': {}})
        ti_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Mi", 'index': index, 'level': "L2.0", 'properties': {}})
        mi_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Square Wave", 'index': index, 'level': "L2.0", 'properties': {}})
        square_wave_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Predictor", 'index': index, 'level': "L2.0", 'properties': {}})
        predictor_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Spike", 'index': index, 'level': "L2.0", 'properties': {}})
        spike_index = index
        index = index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Line", 'index': index, 'level': "L2.0", 'properties': {}})
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
        json_for_neo4j["relation_triplets"].append([square_wave_index, 'intension', time_series_index, {}])
        json_for_neo4j["relation_triplets"].append([spike_index, 'intension', time_series_index, {}])
        json_for_neo4j["relation_triplets"].append([line_index, 'intension', time_series_index, {}])

        # line ts
        for line_ts in output_data_dict["Line"]:
            json_for_neo4j["nodes"].append({'name': line_ts, 'index': index, 'level': 'L1', 'properties': {}})

            json_for_neo4j["relation_triplets"].append([index, 'intension', line_index, {}])
            index = index + 1

        # spike ts
        for spike_ts in output_data_dict["Spike"]:
            json_for_neo4j["nodes"].append({'name': spike_ts, 'index': index, 'level': 'L1', 'properties': {}})

            json_for_neo4j["relation_triplets"].append([index, 'intension', spike_index, {}])
            index = index + 1

        # square ts
        for square_ts in output_data_dict["Square"]:
            json_for_neo4j["nodes"].append({'name': square_ts, 'index': index, 'level': 'L1', 'properties': {}})

            json_for_neo4j["relation_triplets"].append([index, 'intension', square_wave_index, {}])
            index = index + 1

        # analysis parameters
        metadata_dict = output_data_dict["metadata"]["parameters"]
        metadata_dict["start_ts"] = str(output_data_dict["metadata"]["start_ts"])
        metadata_dict["end_ts"] = str(output_data_dict["metadata"]["end_ts"])
        metadata_dict["min_ts"] = str(output_data_dict["metadata"]["min_ts"])
        metadata_dict["max_ts"] = str(output_data_dict["metadata"]["max_ts"])
        metadata_dict["filters"] = ','.join(metadata_dict["filters"])

        json_for_neo4j["nodes"].append({'name': "params", 'index': index, 'level': 'L1', 'properties': metadata_dict})

        json_for_neo4j["relation_triplets"].append([index, 'intension', metadata_index, {}])
        index = index + 1

        temp_analyzed_dict = {}
        # analyzed together with regimes
        for idx, analyze in enumerate(output_data_dict["Analyzed"]):

            analyze_name = analyze

            curr_analyzed_index = index
            json_for_neo4j["nodes"].append(
                {'name': analyze_name, 'index': index, 'level': 'L1', 'properties': {}})
            index = index + 1

            temp_analyzed_dict[analyze_name] = curr_analyzed_index

            json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'intension', analyzed_index, {}])

            if idx < len(output_data_dict["all_regimes"]):
                millisecond_regimes = output_data_dict["all_regimes"][idx]
                curr_regime_index = index
                json_for_neo4j["nodes"].append(
                    {'name': f"Regime{loop_no}_{idx + 1}", 'index': index, 'level': 'L1', 'properties': {
                        "regime": ",".join([str(x) for x in millisecond_regimes])
                    }})

                index = index + 1
                json_for_neo4j["relation_triplets"].append([curr_regime_index, 'intension', regime_index, {}])
                json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_regime_index, {}])

        # events
        for idx in range(len(output_data_dict["indicators"]["leading indicator"])):

            json_for_neo4j["nodes"].append(
                {'name': f"Event{loop_no}_{idx + 1}", 'index': index, 'level': 'L1', 'properties': {}})
            curr_event_index = index

            json_for_neo4j["relation_triplets"].append([curr_event_index, 'intension', unclassified_event_index, {}])

            index = index + 1
            event_leading_indicator_list = output_data_dict["indicators"]["leading indicator"][str(idx)]
            event_main_indicator_list = output_data_dict["indicators"]["main indicator"][str(idx)]
            event_trailing_indicator_list = output_data_dict["indicators"]["trailing indicator"][str(idx)]

            temp_indicator_dict = {}
            for leading_indicator in event_leading_indicator_list:
                leading_name = leading_indicator

                li_name = leading_name + f"_Event{loop_no}_{idx + 1}"

                json_for_neo4j["nodes"].append({
                    "name": li_name,
                    "level": "L1",
                    "index": index,
                    "properties": {}
                })
                curr_li_index = index
                index = index + 1

                temp_indicator_dict[li_name] = curr_li_index

                json_for_neo4j["relation_triplets"].append([curr_event_index, 'has', curr_li_index, {}])
                json_for_neo4j["relation_triplets"].append([curr_li_index, 'intension', li_index, {}])
                curr_analyzed_index = temp_analyzed_dict[leading_name]
                json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_li_index, {}])

            for main_indicator in event_main_indicator_list:
                main_name = main_indicator

                mi_name = main_name + f"Event{loop_no}_{idx + 1}"

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
                curr_analyzed_index = temp_analyzed_dict[main_name]
                json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_mi_index, {}])

            for trailing_indicator in event_trailing_indicator_list:
                trailing_name = trailing_indicator


                ti_name = trailing_name + f"Event{loop_no}_{idx + 1}"

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
                curr_analyzed_index = temp_analyzed_dict[trailing_name]
                json_for_neo4j["relation_triplets"].append([curr_analyzed_index, 'has', curr_ti_index, {}])

        # contributors
        if len(output_data_dict["contributors"]) > 0:
            for key in output_data_dict["contributors"]["event"]:
                value = output_data_dict["contributors"]["event"][key]
                if value != "no_event":
                    # create contributions
                    contributor_name = output_data_dict["contributors"]["indicator"][key].split(':')[3]
                    contribution_amount = output_data_dict["contributors"]["contribution"][key]

                    contributor = next(
                        (node for node in json_for_neo4j["nodes"] if
                         node["name"] == contributor_name and node["level"] == "L1"),
                        None)

                    if contributor is not None:
                        contributor_ts_node_index = contributor["index"]

                        json_for_neo4j["nodes"].append(
                            {'name': f"{contributor_name}:Event{loop_no}_{value}", 'index': index, 'level': 'L1',
                             'properties': {}})

                        json_for_neo4j["relation_triplets"].append([index, 'intension', predictor_index, {}])
                        json_for_neo4j["relation_triplets"].append(
                            [contributor_ts_node_index, 'contributes', index, {}])
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