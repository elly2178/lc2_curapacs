from flask import jsonify
from kubernetes import config, client
from helpers.curapacsSettings import CurapacsSettings

# loads where is the ip located and how to authenticate (keyphrase)
config.load_kube_config(config_file='/home/schumi/.kube/config')

settings = CurapacsSettings({})

v1 = client.CoreV1Api()

def list_only_Specific():
    ret = v1.list_pod_for_all_namespaces(watch=False)
    #Make a temp list to store all the items in the dictionary
    tempList = []
    for i in ret.items:
        if i.metadata.namespace.startswith(settings.curapacs_namespace_prefix):
            tempList.append({
                "pod_ip":i.status.pod_ip,
                "namespace":i.metadata.namespace,
                "name":i.metadata.name
            })
        else:
            print("No pods with the name ")
      
      
    return jsonify(tempList)