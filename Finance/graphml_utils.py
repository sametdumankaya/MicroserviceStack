import json
import networkx as nx
import numpy as np
import pandas as pd

from fastapi import HTTPException


class GraphmlUtils:
    def __init__(self, neo4j_api_client):
        self.neo4j_api_client = neo4j_api_client

        # self.finance_node_id = self.neo4j_api_client.find_node_id("Finance", "L2.3")
        # 
        # if self.finance_node_id is None:
        #     # creating nodes
        #     self.finance_node_id = self.neo4j_api_client.create_node("Finance", "L2.3")
        #     self.stock_market_node_id = self.neo4j_api_client.create_node("Stock Market", "L2.3")
        #     self.company_node_id = self.neo4j_api_client.create_node("Company", "L2.3")
        #     self.sector_node_id = self.neo4j_api_client.create_node("Sector", "L2.2")
        #     self.industry_node_id = self.neo4j_api_client.create_node("Industry", "L2.2")
        #     self.nasdaq_node_id = self.neo4j_api_client.create_node("Nasdaq", "L2.2")
        # 
        #     # creation relations
        #     self.neo4j_api_client.add_antisymmetric_relation(self.company_node_id, self.stock_market_node_id, "in")
        #     self.neo4j_api_client.add_antisymmetric_relation(self.sector_node_id, self.industry_node_id, "has")
        #     self.neo4j_api_client.add_intension(self.sector_node_id, self.finance_node_id)
        #     self.neo4j_api_client.add_intension(self.industry_node_id, self.finance_node_id)
        #     self.neo4j_api_client.add_intension(self.nasdaq_node_id, self.stock_market_node_id)
        # else:
        #     # getting node ids
        #     self.stock_market_node_id = self.neo4j_api_client.find_node_id("Stock Market", "L2.3")
        #     self.company_node_id = self.neo4j_api_client.find_node_id("Company", "L2.3")
        #     self.sector_node_id = self.neo4j_api_client.find_node_id("Sector", "L2.2")
        #     self.industry_node_id = self.neo4j_api_client.find_node_id("Industry", "L2.2")
        #     self.nasdaq_node_id = self.neo4j_api_client.find_node_id("Nasdaq", "L2.2")

    def create_neo4j_graphl_with_file(self, file_name: str):
        print(file_name)
        if file_name is None or not file_name:
            raise HTTPException(status_code=500, detail=f"Data_type parameter cannot be empty.")

        G = nx.read_graphml(file_name)

        if G is None:
            raise HTTPException(status_code=500, detail=f"There was an error, graphml file was not found.")

        json_for_neo4j = {"nodes": [], "relation_triplets": []}

        node_index = 0

        json_for_neo4j["nodes"].append(
            {'name': "Finance", 'index': node_index, 'level': 'L2.3', 'properties': {}})
        finance_index = node_index
        node_index = node_index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Stock Market", 'index': node_index, 'level': 'L2.3', 'properties': {}})
        stock_market_index = node_index
        node_index = node_index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Company", 'index': node_index, 'level': 'L2.3', 'properties': {}})
        company_node_index = node_index
        node_index = node_index + 1

        json_for_neo4j["nodes"].append({'name': "Sector", 'index': node_index, 'level': 'L2.2',  'properties': {}})
        sector_node_index = node_index
        node_index = node_index + 1

        json_for_neo4j["nodes"].append(
            {'name': "Industry", 'index': node_index, 'level': 'L2.2',  'properties': {}})
        industry_node_index = node_index
        node_index = node_index + 1



        json_for_neo4j["nodes"].append(
            {'name': "Nasdaq", 'index': node_index, 'level': 'L2.2',  'properties': {}})
        nasdaq_node_index = node_index
        node_index = node_index + 1

        intension_relation = "intension"
        has_relation = "has"

        json_for_neo4j["relation_triplets"].append(
            [sector_node_index, intension_relation, finance_index, {}])

        json_for_neo4j["relation_triplets"].append(
            [industry_node_index, intension_relation, finance_index, {}])

        json_for_neo4j["relation_triplets"].append(
            [sector_node_index, has_relation, industry_node_index, {}])

        json_for_neo4j["relation_triplets"].append(
            [company_node_index, "in", stock_market_index, {}])

        json_for_neo4j["relation_triplets"].append(
            [nasdaq_node_index, intension_relation, stock_market_index, {}])

        all_nodes = pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index')

        for index, row in all_nodes.iterrows():
            sector_name = row["sector"]
            symbol_name = row["symbol"]
            industry_name = row['industry']

            if sector_name is not np.nan and symbol_name is not np.nan and industry_name is not np.nan:

                curr_sector = next((node for node in json_for_neo4j["nodes"] if node["name"] == sector_name),
                                   None)

                if curr_sector is None:
                    json_for_neo4j["nodes"].append({
                        "name": sector_name,
                        "level": "L2.1", 
                        "index": node_index,
                        "properties": {}
                    })
                    curr_sector_index = node_index
                    node_index += 1
                    json_for_neo4j["relation_triplets"].append(
                        [curr_sector_index, intension_relation, sector_node_index, {}])
                else:
                    curr_sector_index = curr_sector["index"]

                curr_industry = next((node for node in json_for_neo4j["nodes"] if node["name"] == industry_name),
                                     None)

                if curr_industry is None:
                    json_for_neo4j["nodes"].append({
                        "name": industry_name,
                        "level": "L2.1", 
                        "index": node_index,
                        "properties": {}
                    })
                    curr_industry_index = node_index
                    node_index += 1
                    json_for_neo4j["relation_triplets"].append(
                        [curr_industry_index, intension_relation, industry_node_index, {}])
                    json_for_neo4j["relation_triplets"].append(
                        [curr_sector_index, has_relation, curr_industry_index, {}])
                else:
                    curr_industry_index = curr_industry["index"]

                curr_symbol = next((node for node in json_for_neo4j["nodes"] if node["name"] == symbol_name),
                                   None)

                if curr_symbol is None:
                    json_for_neo4j["nodes"].append({
                        "name": symbol_name,
                        "level": "L2.1", 
                        "index": node_index,
                        "properties": {}
                    })
                    curr_symbol_index = node_index
                    node_index += 1
                else:
                    curr_symbol_index = curr_symbol["index"]

                json_for_neo4j["relation_triplets"].append(
                    [curr_symbol_index, intension_relation, company_node_index, {}])
                json_for_neo4j["relation_triplets"].append(
                    [curr_symbol_index, intension_relation, nasdaq_node_index, {}])
                json_for_neo4j["relation_triplets"].append(
                    [curr_symbol_index, has_relation, curr_industry_index, {}])
                json_for_neo4j["relation_triplets"].append(
                    [curr_symbol_index, has_relation, curr_sector_index, {}])

        return json_for_neo4j