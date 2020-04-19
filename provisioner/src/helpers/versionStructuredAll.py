'''
return all the versions of all the APIs avaiable
'''
from flask import jsonify
from kubernetes import client, config
config.load_kube_config(config_file='/home/schumi/.kube/config')

v1 = client.CoreV1Api()

def getAllVersions():
    tempList= []
    for api in client.ApisApi().get_api_versions().groups:
        versions = []
        for vivi in api.versions:
            name = ""
            if vivi.version == api.preferred_version.version and len(
                    api.versions) > 1:
                name += "*"
            name += vivi.version
            versions.append(name)
        
        print("%-40s %s" % (api.name, ",".join(versions)))
        tempList.append({
            "name": api.name,
            "version":versions
        })
    return jsonify(tempList)
         
#if __name__ == '__main__':
 #    getAllVersions()

 