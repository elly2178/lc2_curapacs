from flask import jsonify
from kubernetes import config, client

# loads where is the ip located and how to authenticate (keyphrase)
config.load_kube_config(config_file='/home/schumi/.kube/config')


v1 = client.CoreV1Api()

def list_namespaces():
    ret = v1.list_pod_for_all_namespaces(watch=False)
    #Make a temp list to store all the items in the dictionary
    tempList = []
    for pod in ret.items:
        # create a newTemp list to save the appended temp list
        tempList.append({
            "pod_ip":pod.status.pod_ip,
            "namespace":pod.metadata.namespace,
            "name":pod.metadata.name})

        
    # return the jsonify verison of the list
    return jsonify(tempList)