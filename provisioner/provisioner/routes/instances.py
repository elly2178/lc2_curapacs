from kubernetes import client
from config import CURAPACS_CONFIG
from helpers.api_response_parser import PodListParser
from flask_restful import Resource, fields, marshal_with



resource_fields = {
    'name': fields.String,
    'pod_ip': fields.String,
    'namespace': fields.String,
}


class OrthancInstancePodList(Resource):
    #@marshal_with(resource_fields, envelope='resource')
    def get(self, **kwargs):
        v1 = client.CoreV1Api()
        response = v1.list_namespaced_pod(CURAPACS_CONFIG["namespace"])
        parser = PodListParser(response)
        return parser.get_pod_list()
    
    def post(self, **kwargs):
        pass
"""
def instances(instance_id=None):
    instance_dict = {}
    pod_list = k8s_corev1.list_namespaced_pod(watch=False, namespace=CURAPACS_CONFIG["namespace"])
    for pod_definition in pod_list.items:
        labels = pod_definition.metadata.labels
        containers = pod_definition.spec.containers
        if labels["curamed.ch/customer"] not in instance_dict:
            instance_dict[labels["curamed.ch/customer"]] = {}
        instance_dict[labels["curamed.ch/customer"]][labels["app.kubernetes.io/name"]] = containers[0].image
    return jsonify(instance_dict)
"""