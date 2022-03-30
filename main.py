"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template
from neo4j import GraphDatabase
from google.cloud import secretmanager
app = Flask(__name__)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app


@app.route('/')
def hello():
    client = secretmanager.SecretManagerServiceClient()

    secret = client.access_secret_version(
                        request={"name": f"projects/caip-growth-experiments/secrets/neo4j1g/versions/1"}
                   )
    if len(secret.payload.data) > 0:
        result = 'Secret Found ' + len(secret.payload.data)
    else:
        result = "Error"
    return result

if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '8080'))
    except ValueError:
        PORT = 8080
    app.run(HOST, PORT, debug=True)
