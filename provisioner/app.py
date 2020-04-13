from kubernetes import config, client
# put inside here flask
# loads where is the ip located and how to authenticate (keyphrase)
config.load_kube_config(config_file='/home/schumi/.kube/config')

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")

#ret = v1.list_pod_for_all_namespaces(watch=False)
#for i in ret.items:
#    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

ret = v1.list_namespaced_pod('pacsaas-c0100')
# print the first item if the list of dictonary. GEt the name of the metadata of that first item list
print(ret.items[0].metadata.name)
# output: meddream-viewwer-deployment-...


# tuts: do the tutorial on watch
# deploy with  kubectl apply -f orthanc/manifest.yml but have to this in python
# go to github and create a project whre we put our shit and we push therer 
#  make the crud py rutorial
# def crete deplyment ---- namespace = "c-0100 cred"

ret2 = v1.list_namespace()
nslist = []
for namespace in ret2.items:
    nslist.append(namespace.metadata.name)
    #print(namespace.metadata.name=='pacsaas-c0100')
#print(namespace)
for namespace in nslist:
    if namespace.startswith('pacsaas'):
        print("woogabooga " + namespace)

    