"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template
from neo4j import GraphDatabase
from google.cloud import secretmanager
import math
app = Flask(__name__)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app


def get_data(pwd):
    driver = GraphDatabase.driver("neo4j+s://f9e63c88.databases.neo4j.io:7687", auth=("neo4j", pwd))
    try:
        with driver.session() as session:
            data = session.read_transaction(_get_graph)
            return data
    except:
        driver.close()
        raise

def _render_service(service: str):
    return service.replace("google.cloud.aiplatform.","").rsplit(".",1)[0]

def _format_node(node):
    return '{ "id":' + str(node.id) + ', "label": "' + _render_service(node["api_method"]) +'"}'

def _format_edge(edge):
    count = math.log10(edge["count"]) 
    return '{ "from":' + str(edge.nodes[0].id) + ', "to":' + str(edge.nodes[1].id) + ', "value": "' + str(count) +'", "arrows": {"to":{"enabled":true,  "scalefactor" : 0.1 } } }'

def _get_graph(tx):
    src = tx.run('match (api:ApiMethod {service:"PipelineService"})-[:NEXT1]->(:ApiMethod {service:"JobService"}) return distinct api')
    dst = tx.run('match (:ApiMethod {service:"PipelineService"})-[:NEXT1]->(api:ApiMethod {service:"JobService"}) return distinct api')
    edges = tx.run('match (:ApiMethod {service:"PipelineService"})-[nx:NEXT1]->(:ApiMethod {service:"JobService"}) return distinct nx')
    return ' '.join([
                    '{"nodes":[',
                     ','.join([ _format_node(record["api"]) for record in src]),
                    ",",
                    ','.join([ _format_node(record["api"]) for record in dst]),
                    '],"edges":[',
                    ','.join([_format_edge(record["nx"]) for record in edges]),
                    ']}'
                    ])


@app.route('/')
def hello():
    
    client = secretmanager.SecretManagerServiceClient()

    secret = client.access_secret_version(
                        request={"name": f"projects/caip-growth-experiments/secrets/neo4j8g/versions/1"}
                   )
    pwd = secret.payload.data.decode('ascii')
    
    graph_data = get_data(pwd)
    return render_template("main.html", graph_data=graph_data)

if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '8080'))
    except ValueError:
        PORT = 8080
    app.run(HOST, PORT, debug=True)
