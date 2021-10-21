import requests


class Neo4jClient:
    def __init__(self, url):
        self.url = url

    def create_node(self, name: str, level: str, properties: dict = None):
        response = requests.post(f'{self.url}/create_node',
                                 json={
                                     "name": name,
                                     "level": level,
                                     "properties": properties if properties is not None else {}
                                 }).json()
        return response["node_id"]

    def find_node_id(self, name: str, level: str):
        response = requests.post(f'{self.url}/find_node_id',
                                 json={
                                     "name": name,
                                     "level": level
                                 }).json()
        return response["node_id"]

    def add_antisymmetric_relation(self, start_node_id: int, end_node_id: int, relation_name: str,
                                   relation_properties: dict = None):
        if relation_properties is None:
            relation_properties = {}
        response = requests.post(f'{self.url}/add_antisymmetric_relation',
                                 json={
                                     "start_node_id": start_node_id,
                                     "end_node_id": end_node_id,
                                     "relation_name": relation_name,
                                     "relation_properties": relation_properties if
                                     relation_properties is not None else {}
                                 }).json()
        return response["relationship_id"]

    def add_intension(self, start_node_id: int, end_node_id: int, relation_properties: dict = None):
        response = requests.post(f'{self.url}/add_intension',
                                 json={
                                     "start_node_id": start_node_id,
                                     "end_node_id": end_node_id,
                                     "relation_properties": relation_properties if
                                     relation_properties is not None else {}
                                 }).json()
        return response["relationship_id"]

    def add_extension(self, start_node_id: int, end_node_id: int, relation_properties: dict = None):
        response = requests.post(f'{self.url}/add_extension',
                                 json={
                                     "start_node_id": start_node_id,
                                     "end_node_id": end_node_id,
                                     "relation_properties": relation_properties if
                                     relation_properties is not None else {}
                                 }).json()
        return response["relationship_id"]

    def add_symmetric_relation(self, start_node_id: int, end_node_id: int, relation_name: str,
                               relation_properties: dict = None):
        response = requests.post(f'{self.url}/add_symmetric_relation',
                                 json={
                                     "start_node_id": start_node_id,
                                     "end_node_id": end_node_id,
                                     "relation_name": relation_name,
                                     "relation_properties": relation_properties if
                                     relation_properties is not None else {}
                                 }).json()
        return response["relationship_id"]

    def follows_temporally(self, start_node_id: int, end_node_id: int, how_many: int, how_long: str = None,
                           contribution_amount: int = None):
        response = requests.post(f'{self.url}/follows_temporally',
                                 json={
                                     "start_node_id": start_node_id,
                                     "end_node_id": end_node_id,
                                     "how_long": how_long,
                                     "how_many": how_many,
                                     "contribution_amount": contribution_amount
                                 }).json()
        return response["relationship_id"]

    def export_db_to_graphml(self):
        response = requests.post(f'{self.url}/export_db_to_graphml').json()
        return response["file_path"]

    def create_graph(self, graph_dict: dict):
        response = requests.post(f'{self.url}/create_graph',
                                 json={
                                     "graph_dict": graph_dict
                                 }).json()
        return response["node_ids"]

    def create_graph_nx(self, zip_name: str, merge_node_levels: str):
        fileobj = open(f'{zip_name}', 'rb')
        r = requests.post(f'{self.url}/create_graph_nx', data={"merge_nodes_level": merge_node_levels},
                          files={"zip_file": (f"{zip_name}", fileobj)})

        return r

    def create_news_graph(self, graph_dict: dict, merge_nodes_level: str):
        response = requests.post(f'{self.url}/create_graph',
                                 json={
                                     "graph_dict": graph_dict,
                                     "merge_nodes_level": merge_nodes_level
                                 }).json()
        return response
