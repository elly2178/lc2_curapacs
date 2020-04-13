from flask import jsonify
from kubernetes import config, client

# loads where is the ip located and how to authenticate (keyphrase)
config.load_kube_config(config_file='/home/schumi/.kube/config')


v1 = client.CoreV1Api()

def list_namespaces():
    ret = v1.list_pod_for_all_namespaces(watch=False)
    #Make a temp list to store all the items in the dictionary
    tempList = []
    for i in ret.items:
        # create a newTemp list to save the appended temp list
        #tempList.append("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        tempList.append({
            "pod_ip":i.status.pod_ip,
            "namespace":i.metadata.namespace,
            "name":i.metadata.name})
    # return the jsonify verison of the list
    return jsonify(tempList)