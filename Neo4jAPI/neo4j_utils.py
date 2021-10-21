import datetime
import time

from py2neo import Graph, Relationship, Node
import os
import uuid
import networkx as nx
from shutil import move


class Neo4jUtils:
    def __init__(self):

        self.host = os.getenv("neo4j_host", "localhost")
        # temple edit
        # self.port = int(os.getenv("neo4j_port", "7688"))
        self.port = int(os.getenv("neo4j_port", "7687"))
        self.user = os.getenv("neo4j_user", "neo4j")
        self.password = os.getenv("neo4j_password", "magi")
        counter = 0
        while True:
            try:
                if counter % 10000 == 0:
                    print(f"Trying to connect neo4j at host: {self.host}, port: {self.port}")
                self.graph = Graph(host=self.host, port=self.port, user=self.user, password=self.password)
                print("Connected!")
                self.graph.run("CREATE INDEX magi_index IF NOT EXISTS FOR (n:magi) ON (n.magi_display_name)")
                break
            except:
                if counter % 10000 == 0:
                    print("Connection failed. Trying again")
                counter += 1
                time.sleep(5)
                continue
        try:
            self.graph.schema.create_index("magi", "level")
        except:
            pass

    def __commit_transaction(self, entity):
        transaction = self.graph.begin()
        transaction.create(entity)
        transaction.commit()

    def __create_relationship(self, start_node: Node, end_node: Node, relation_name: str, relation_properties: dict):
        relationship = Relationship(start_node, relation_name, end_node)
        relation_properties['magi_insert_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for key, value in relation_properties.items():
            relationship[key] = value
        self.__commit_transaction(relationship)
        return relationship

    def create_node(self, name: str, level: str, properties: dict):
        if not level:
            raise ValueError("Level must be provided.")
        if level.upper().startswith("L2"):
            existing_node = self.graph.nodes.match(name, level=level).first()
            if existing_node is not None:
                return existing_node
        properties['level'] = level.upper()
        properties['magi_display_name'] = name
        properties['magi_insert_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        node = Node("magi", name, **properties)
        self.__commit_transaction(node)
        return node

    def get_node_by_id(self, node_id: int):
        return self.graph.nodes.get(node_id)

    def find_node_id(self, name: str, level: str):
        match = self.graph.nodes.match(name, level=level).first()
        return match.identity if match is not None else None

    def add_antisymmetric_relation(self, start_node: Node, end_node: Node, relation_name: str,
                                   relation_properties: dict):
        start_node_level = start_node["level"]
        end_node_level = end_node["level"]
        if start_node_level != end_node_level:
            raise ValueError("Cannot add antisymmetric relation between two nodes with different levels.")
        relation = self.__create_relationship(start_node, end_node, relation_name, relation_properties)
        return relation

    def add_intension(self, start_node: Node, end_node: Node, relation_properties: dict):
        start_node_levels = start_node["level"].split(".")
        end_node_levels = end_node["level"].split(".")

        if int(start_node_levels[0][1:]) > int(end_node_levels[0][1:]):
            raise ValueError("Level of start node cannot be greater than the level of end node.")

        if len(start_node_levels) == 2 and len(end_node_levels) == 2:
            if int(start_node_levels[1]) >= int(end_node_levels[1]):
                raise ValueError("Level of start node cannot be greater than or equal to the level of end node.")

        intension = self.__create_relationship(start_node, end_node, "intension", relation_properties)
        return intension

    def add_extension(self, start_node: Node, end_node: Node, relation_properties: dict):
        start_node_levels = start_node["level"].split(".")
        end_node_levels = end_node["level"].split(".")

        if int(start_node_levels[0][1:]) < int(end_node_levels[0][1:]):
            raise ValueError("Level of start node cannot be less than the level of end node.")

        if len(start_node_levels) == 2 and len(end_node_levels) == 2:
            if int(start_node_levels[1]) <= int(end_node_levels[1]):
                raise ValueError("Level of start node cannot be less than or equal to the level of end node.")

        extension = self.__create_relationship(start_node, end_node, "extension", relation_properties)
        return extension

    def add_symmetric_relation(self, start_node: Node, end_node: Node, relation_name: str, relation_properties: dict):
        if start_node["level"] != end_node["level"]:
            raise ValueError("Cannot add symmetric relation between two nodes with different levels.")
        relation1 = self.__create_relationship(start_node, end_node, relation_name, relation_properties)
        relation2 = self.__create_relationship(end_node, start_node, relation_name, relation_properties)
        return relation1, relation2

    def follows_temporally(self, start_node: Node, end_node: Node, how_many: int, how_long: str,
                           contribution_amount: float):
        if start_node["level"] != end_node["level"]:
            raise ValueError("Cannot add symmetric relation between two nodes with different levels.")
        # create the relation bw start_node and end_node if it does not exist
        # if exists, concat how_many and how_long to the attributes as a string
        relations = self.graph.match([start_node, end_node], r_type='followsTemporally').all()
        if len(relations) == 0:
            new_relation = self.__create_relationship(start_node, end_node, "followsTemporally",
                                                      relation_properties={"how_many": how_many,
                                                                           "how_long": how_long,
                                                                           "contribution_amount": contribution_amount})
            return new_relation
        else:
            relations[0]["how_many"] += how_many
            if how_long and len(how_long) > 0:
                relations[0]["how_long"] = relations[0]["how_long"] + "," + how_long
            self.graph.push(relations[0])
            return relations[0]

    def export_db_to_graphml(self):
        file_name = str(uuid.uuid4())
        self.graph.run(
            f"CALL apoc.export.graphml.all('/data/{file_name}.graphml', {{useTypes:true, storeNodeIds:false}})").data()
        file_path = f"/data/{file_name}.graphml"
        self.clean_db()
        return file_path

    def clean_db(self):
        result = self.graph.run("match (n) detach delete n").data()
        return result

    def create_graph_nx(self, graph_dict: dict, merge_nodes_level: str):
        creation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        graph = nx.MultiDiGraph()
        for node in graph_dict["nodes"]:
            graph.add_node(node["name"] + "_" + node["level"],
                           labels=f":magi",
                           magi_display_name=node["name"],
                           insert_date=creation_date,
                           level=str(node["level"]).strip().upper(),
                           **node["properties"])

        for relation_triplets in graph_dict["relation_triplets"]:
            graph.add_edge(
                graph_dict["nodes"][relation_triplets[0]]["name"] + "_" + graph_dict["nodes"][relation_triplets[0]][
                    "level"],
                graph_dict["nodes"][relation_triplets[2]]["name"] + "_" + graph_dict["nodes"][relation_triplets[2]][
                    "level"],
                labels=relation_triplets[1],
                magi_display_name=relation_triplets[1],
                insert_date=creation_date,
                **relation_triplets[3])

        local_graphml_name = f"{str(uuid.uuid4())}.graphml"
        nx.write_graphml_lxml(graph, local_graphml_name, named_key_ids=True)
        move(local_graphml_name, f"/data/{local_graphml_name}")
        self.graph.run(
            f'CALL apoc.import.graphml("/data/{local_graphml_name}", {{readLabels: true, storeNodeIds:true}})').data()
        self.merge_nodes(merge_nodes_level)
        os.remove(f"/data/{local_graphml_name}")
        return True

    def merge_nodes(self, level: str):
        self.graph.run(
            f'MATCH (n1),(n2) WHERE n1.magi_display_name = n2.magi_display_name and n1.level = n2.level and n1.level starts with "{str(level).strip().upper()}" and id(n1) < id(n2) WITH [n1,n2] as ns CALL apoc.refactor.mergeNodes(ns,{{properties:"overwrite", mergeRels: "true"}}) yield node RETURN true')

    def search_graph_for_nlp(self, text: str):
        result = []
        nodes = self.graph.nodes.match().where(f"_.magi_display_name =~ '(?i){text.strip()}'").all()
        for node in nodes:
            relationships = self.graph.match(r_type=None, nodes=(node, None)).all()
            for rel in relationships:
                result.append({
                    "relation": type(rel).__name__,
                    "end_node": rel.end_node["magi_display_name"]
                })
        return result
