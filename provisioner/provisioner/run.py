from flask import Flask
from helpers import k8s_config, config
from routes.instances import OrthancInstancePodList
from flask_restful import reqparse, abort, Api, Resource

k8s_config.load_kubernetes_config()
app = Flask(__name__)
api = Api(app)

api.add_resource(OrthancInstancePodList, '/instances')

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()