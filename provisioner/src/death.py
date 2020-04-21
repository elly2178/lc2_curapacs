# this is a way, to find out all the attributes of all the pods. this is for dev. only. once the provisioner will be given away,
# DELETE THIS SHIT
from kubernetes import client, config

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_pod_for_all_namespaces(watch=False)
print(ret)
#for i in ret.items:
    #print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    