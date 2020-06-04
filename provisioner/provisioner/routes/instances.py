from kubernetes import client
from flask_restful import Resource, fields, marshal_with, reqparse
from helpers.config import CURAPACS_CONFIG, CURAPACS_K8S_COMPONENTS
from helpers.api_response_parser import PodListParser
from helpers.instance_creator import manipulate_components


reqparser = reqparse.RequestParser()
reqparser.add_argument('curapacs_customer', type=str, help='customer designation, e.g. c0100, c0594 ...', required=True)
reqparser.add_argument('components', type=str, help=f'Comma separated list, component name in: {CURAPACS_K8S_COMPONENTS.keys()}', default="")

class OrthancInstancePodList(Resource):
    def get(self, **kwargs):
        v1 = client.CoreV1Api()
        response = v1.list_namespaced_pod(CURAPACS_CONFIG["namespace"])
        parser = PodListParser(response)
        return parser.get_pod_list(), 200
    
    def post(self, **kwargs):
        print(str(kwargs))
        args = reqparser.parse_args(strict="true")
        curapacs_components = args.components.split(",") if args.components else []
        manipulate_components(args.curapacs_customer, mode="apply", components=curapacs_components)
        return {}, 200 
    
    def delete(self, **kwargs):
        args = reqparser.parse_args(strict="true")
        curapacs_components = args.components.split(",") if args.components else []
        manipulate_components(args.curapacs_customer, mode="delete", components=curapacs_components)
        return {}, 200 