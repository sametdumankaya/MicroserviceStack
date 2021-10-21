from neo4j_api_client import Neo4jApiClient
import json
import requests
from allennlp_models import pretrained
import nltk

nltk.download('punkt')


class MetamodelUtils:
    def __init__(self, neo4j_api_port: int, stanford_nlp_port: int):
        self.client = Neo4jApiClient(f"http://localhost:{neo4j_api_port}")
        self.question_count = 1
        self.doc_count = 1
        self.stanford_nlp_port = stanford_nlp_port
        self.predictor = pretrained.load_predictor("coref-spanbert")
        # Initial nodes
        self.natural_language_node_id = self.client.find_node_id("Natural Language", "L2.2")
        if self.natural_language_node_id is None:
            self.natural_language_node_id = self.client.create_node("Natural Language", "L2.2")
            self.sentence_node_id = self.client.create_node("Sentence", "L2.2")
            self.document_node_id = self.client.create_node("Document", "L2.1")
            self.question_node_id = self.client.create_node("Question", "L2.1")
            self.declarative_node_id = self.client.create_node("Declarative", "L2.1")
            self.semantic_parse_node_id = self.client.create_node("Semantic Parse", "L2.1")
            self.polar_node_id = self.client.create_node("Polar", "L2.0")
            self.what_node_id = self.client.create_node("What", "L2.0")
            self.when_node_id = self.client.create_node("When", "L2.0")
            self.where_node_id = self.client.create_node("Where", "L2.0")
            self.who_node_id = self.client.create_node("Who", "L2.0")
            self.which_node_id = self.client.create_node("Which", "L2.0")
            self.why_node_id = self.client.create_node("Why", "L2.0")
            self.how_node_id = self.client.create_node("How", "L2.0")
            self.whose_node_id = self.client.create_node("Whose", "L2.0")
            self.whom_node_id = self.client.create_node("Whom", "L2.0")

            self.client.add_antisymmetric_relation(self.natural_language_node_id, self.sentence_node_id, "has")
            self.client.add_intension(self.document_node_id, self.natural_language_node_id)
            self.client.add_antisymmetric_relation(self.document_node_id, self.question_node_id, "has")
            self.client.add_antisymmetric_relation(self.document_node_id, self.declarative_node_id, "has")
            self.client.add_antisymmetric_relation(self.question_node_id, self.semantic_parse_node_id, "has")
            self.client.add_intension(self.question_node_id, self.sentence_node_id)
            self.client.add_intension(self.declarative_node_id, self.natural_language_node_id)
            self.client.add_intension(self.declarative_node_id, self.sentence_node_id)
            self.client.add_antisymmetric_relation(self.declarative_node_id, self.semantic_parse_node_id, "has")
            self.client.add_intension(self.polar_node_id, self.question_node_id)
            self.client.add_intension(self.what_node_id, self.question_node_id)
            self.client.add_intension(self.when_node_id, self.question_node_id)
            self.client.add_intension(self.where_node_id, self.question_node_id)
            self.client.add_intension(self.who_node_id, self.question_node_id)
            self.client.add_intension(self.which_node_id, self.question_node_id)
            self.client.add_intension(self.why_node_id, self.question_node_id)
            self.client.add_intension(self.how_node_id, self.question_node_id)
            self.client.add_intension(self.whose_node_id, self.question_node_id)
            self.client.add_intension(self.whom_node_id, self.question_node_id)
        else:
            self.sentence_node_id = self.client.find_node_id("Sentence", "L2.2")
            self.document_node_id = self.client.find_node_id("Document", "L2.1")
            self.question_node_id = self.client.find_node_id("Question", "L2.1")
            self.declarative_node_id = self.client.find_node_id("Declarative", "L2.1")
            self.semantic_parse_node_id = self.client.find_node_id("Semantic Parse", "L2.1")
            self.polar_node_id = self.client.find_node_id("Polar", "L2.0")
            self.what_node_id = self.client.find_node_id("What", "L2.0")
            self.when_node_id = self.client.find_node_id("When", "L2.0")
            self.where_node_id = self.client.find_node_id("Where", "L2.0")
            self.who_node_id = self.client.find_node_id("Who", "L2.0")
            self.which_node_id = self.client.find_node_id("Which", "L2.0")
            self.why_node_id = self.client.find_node_id("Why", "L2.0")
            self.how_node_id = self.client.find_node_id("How", "L2.0")
            self.whose_node_id = self.client.find_node_id("Whose", "L2.0")
            self.whom_node_id = self.client.find_node_id("Whom", "L2.0")

    def process_text_with_pipelines(self, text: str, pipelines):
        annot = ",".join([pipeline.strip().lower() for pipeline in pipelines])
        url = f'http://localhost:{self.stanford_nlp_port}/'
        params = {'properties': '{"annotators": "' + annot + '"}'}
        r = requests.post(url, data=text.encode('utf-8'), params=params, timeout=60)
        annotations = json.loads(r.text)
        return annotations

    def create_question_graph(self, subject_names, relation_names, object_names, question_keyword: str):
        current_question_node_id = self.client.create_node(f"Question{self.question_count}", "L1")
        question_keyword_node_id = self.client.find_node_id(question_keyword.title(), "L2.0")
        self.client.add_intension(current_question_node_id, question_keyword_node_id)
        for subject_name, relation_name, object_name in zip(subject_names, relation_names, object_names):
            subject_node_id = self.client.create_node(subject_name, "L1")
            object_node_id = self.client.create_node(object_name, "L1")
            self.client.add_antisymmetric_relation(subject_node_id, object_node_id, relation_name)
            self.client.add_antisymmetric_relation(current_question_node_id, subject_node_id, "has")
            self.client.add_antisymmetric_relation(current_question_node_id, object_node_id, "has")
        self.question_count += 1

    def process_question_to_graph(self, text: str):
        splitted = text.split(" ")
        tmp_text = text
        subject_string = ""
        # change the question keyword with a subject, since corenlp cannot properly parse questions
        if splitted[0].lower() == "what":
            tmp_text = "it" + text[4:]
            question_keyword = "What"
            subject_string = "?x"
        elif splitted[0].lower() == "who":
            tmp_text = "She" + text[3:]
            question_keyword = "Who"
            subject_string = "?x"
        elif splitted[0].lower() == "where":
            tmp_text = "Here" + text[5:]
            question_keyword = "Where"
            subject_string = "?x"
        else:
            question_keyword = "Polar"
        annotations = self.process_text_with_pipelines(tmp_text, ["openie", "pos", "ner", "depparse"])

        if len(annotations["sentences"][0]["openie"]) > 0:
            triplets = annotations["sentences"][0]["openie"]
            if triplets and len(triplets) > 0:
                self.create_question_graph([subject_string if subject_string else x["subject"] for x in triplets],
                                           [x["relation"] for x in triplets],
                                           [x["object"] for x in triplets],
                                           question_keyword)
        return annotations

    def create_nlp_graph(self, text: str):
        resolved = self.predictor.coref_resolved(
            document=text
        )

        props = {
            'annotators': 'coref,openie',
            'pipelineLanguage': 'en',
            'outputFormat': 'json',
            'openie.resolve_coref': True
        }

        annotations = requests.post(f'http://localhost:{self.stanford_nlp_port}',
                                    params={'properties': str(props)},
                                    json=resolved).json()
        graph_dict = {
            "nodes": [],
            "relation_triplets": []
        }

        current_document_node_id = self.client.create_node(f"Document {self.doc_count}", "L1")
        self.client.add_intension(current_document_node_id, self.document_node_id)
        node_index = 0
        sentence_relations = {}
        for idx, sentence in enumerate(annotations["sentences"]):
            current_sentence_node_id = self.client.create_node(f"Sentence {idx + 1}", "L1")
            self.client.add_antisymmetric_relation(current_document_node_id, current_sentence_node_id, "has")
            sentence_relations[current_sentence_node_id] = []
            openie_triplets = sentence["openie"]
            for triplet in openie_triplets:
                relation_name = triplet["relation"]
                existing_subject = next((node for node in graph_dict["nodes"] if node["name"] == triplet["subject"]),
                                        None)
                existing_object = next((node for node in graph_dict["nodes"] if node["name"] == triplet["object"]),
                                       None)
                if existing_subject is None:
                    graph_dict["nodes"].append({
                        "name": triplet["subject"],
                        "level": "L1",
                        "index": node_index,
                        "properties": {}
                    })
                    relation_subject_index = node_index
                    node_index += 1
                else:
                    relation_subject_index = existing_subject["index"]

                if existing_object is None:
                    graph_dict["nodes"].append({
                        "name": triplet["object"],
                        "level": "L1",
                        "index": node_index,
                        "properties": {}
                    })
                    relation_object_index = node_index
                    node_index += 1
                else:
                    relation_object_index = existing_object["index"]

                graph_dict["relation_triplets"].append(
                    [relation_subject_index, relation_name, relation_object_index, {}])
                sentence_relations[current_sentence_node_id].append(relation_subject_index)
                sentence_relations[current_sentence_node_id].append(relation_object_index)

        result = self.client.create_graph(graph_dict)
        for sentence_id in sentence_relations:
            for item in list(set(sentence_relations[sentence_id])):
                self.client.add_antisymmetric_relation(sentence_id, result[item], "has")
        self.doc_count += 1
        return result

    def search_in_graph(self, text: str):
        result = self.client.search_graph_for_nlp(text)
        return result

    def export_db_to_graphml(self):
        file_path = self.client.export_db_to_graphml()
        return file_path


    def AmbiverseEntity(self, sentence):
        # 1. get entities
        # cmd = """curl --request POST --url http://localhost:8081/factextraction/analyze   --header 'accept: application/json'   --header 'content-type: application/json'   --data '{"docId": "doc1", "text": "%s", "extractConcepts": "true", "language" : "en" }'"""
        # ret = self.invoke(cmd % sentence)

        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

        data = '{"docId": "doc1", "text": "%s", "extractConcepts": "true", "language" : "en" }' % sentence

        response = requests.post('http://localhost:8081/factextraction/analyze', headers=headers, data=data)

        responseJson = json.loads(response.content)
        if "matches" in responseJson:
            matches = responseJson["matches"]
        if "entities" in responseJson:
            entities = responseJson["entities"]
        names = {}
        # 2. retrieve KB nodes
        for entity in entities:  # first, deal with the *c
            names[entity["id"]] = entity["name"]
        for match in matches:
            if match["text"].islower() and len(match["entity"]) > 0:
                names[match["entity"]["id"]] = names[match["entity"]["id"]].lower()
        return (matches, names)


    def ConceptNetEntity(self, term):
        for side in ["start"]:
            req = requests.get("http://api.conceptnet.io/query?" + side + "=/c/en/" + term + "&rel=/r/IsA&limit=1")
        return req.json()["edges"]


    def ConstructNewsMetamodel(self, news):
        newsDocId = self.client.create_node(news, "L1")
        self.client.add_intension(newsDocId, self.document_node_id)
        splittedNews = nltk.tokenize.sent_tokenize(news)
        for sn in splittedNews:
            if not sn == '':
                sentenceNodeId = self.client.create_node(sn, "L1")
                self.client.add_antisymmetric_relation(newsDocId, sentenceNodeId, "has")
                newsEntities = self.AmbiverseEntity(sn)
                for entity in newsEntities[0]:
                    entityNodeId = self.client.create_node(entity["text"], "L1")
                    self.client.add_antisymmetric_relation(sentenceNodeId, entityNodeId, "has")
                    concepts = self.ConceptNetEntity(entity["text"].lower())
                    for concept in concepts:
                        conceptNodeId = self.client.create_node(concept["end"]["label"], "L1")
                        self.client.add_antisymmetric_relation(entityNodeId, conceptNodeId, "is")
                        print(concept["end"]["label"])


