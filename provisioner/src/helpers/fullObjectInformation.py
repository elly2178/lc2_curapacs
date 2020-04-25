from flask import jsonify
from kubernetes import config, client

# loads where is the ip located and how to authenticate (keyphrase)
config.load_kube_config(config_file='/home/schumi/.kube/config')


v1 = client.CoreV1Api()
def post_fullobjectinformation():
    pass

def get_fullobjectinformation():
    ret = v1.list_pod_for_all_namespaces(watch=False)
     
    # return the jsonify verison of the list
    return jsonify(str(ret))