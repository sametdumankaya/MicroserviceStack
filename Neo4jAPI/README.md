# Neo4j API

This repository contains the neo4j api code. It exposes an interface to create nodes and relationships on neo4j graph db. 
## Installing
Project is developed using Python 3.6.

Install the required packages with the command below
<pre>pip install -r requirements.txt</pre>
API expects a neo4j instance running on localhost. You can configure neo4j connection in the file neo4j_utils.py

Create a directory named "neo4j_data" under your user's root folder
<pre>mkdir neo4j_data</pre>

Make the folder available to everyone
<pre>sudo chmod 777 neo4j_data/</pre>

You can deploy a neo4j instance locally using docker command below. After deploying neo4j, you can browse it on http://localhost:7474
<pre>docker run --publish=7474:7474 --publish=7687:7687 --env=NEO4J_AUTH=neo4j/magi --env='NEO4JLABS_PLUGINS=["apoc"]' --env=NEO4J_apoc_export_file_enabled=true --env=NEO4J_apoc_import_file_enabled=true --env=NEO4J_apoc_import_file_use__neo4j__config=false --volume=$HOME/neo4j_data:/data neo4j</pre>

Run the below command to run the API
<pre>python api.py</pre>


## Accessing API
Visit http://localhost:8003/docs to browse API methods.

## Sample Requests
Sample request bodies (JSON) can be found under sample_request folder for each API Method.