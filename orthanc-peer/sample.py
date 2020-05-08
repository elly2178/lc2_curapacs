import json
import base64
import sys
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import orthanc

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(message)s'))
LOGGER.addHandler(handler)

PEER_NAME = "c0100-orthanc"
PEER_DOMAIN = "curapacs.ch"
ORTHANC_URI = "http://c0100-orthanc.curapacs.ch"
HTTP_USER = "orthanc"
HTTP_PASSWORD = "orthanc"

def post_data(url, data, headers={'Content-Type':'application/json'}):
    LOGGER.debug(f"post_data called with args: {url} and headers {headers}")
    bindata = data if isinstance(data, bytes) else data.encode('utf-8')
    req = Request(url, bindata, headers)
    resp = urlopen(req)
    return json.loads(resp.read().decode()), resp.getheaders()

def get_data(url, headers={'Content-Type':'application/json'}, timeout=3):
    LOGGER.debug(f"get_data called with args: {url} and headers {headers}")
    req = Request(url, headers=headers)
    resp = urlopen(req, timeout=timeout)
    if "Content-Type" in headers.keys() and headers["Content-Type"] == "application/json":
        answer_content = json.loads(resp.read().decode())
        answer_headers = resp.getheaders()
        LOGGER.debug(f"get_data got response with headers: {answer_headers}")
        return answer_content, answer_headers
    return resp.read(), resp.getheaders()

def get_http_auth_header(username, password):
    b64string = base64.b64encode(bytes("{}:{}".format(username, password), encoding="utf-8"))
    return {"Authorization": "Basic {}".format(b64string.decode())}

def getOrthancResource(resource_type, resource_id, orthanc_uri=ORTHANC_URI):
    LOGGER.debug(f"getOrthancResource called with args: {resource_type}, {resource_id} and orthanc_uri {orthanc_uri}")
    headers = {'Content-Type':'application/json'}
    headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    if resource_type == "Study":
        return get_data("{}/studies/{}".format(orthanc_uri, resource_id), headers=headers)
    elif resource_type == "Series":
        return get_data("{}/series/{}".format(orthanc_uri, resource_id), headers=headers)

def getOrthancInstances(orthanc_uri=ORTHANC_URI):
    LOGGER.debug(f"getOrthancInstances called with args: orthanc_uri {orthanc_uri}")
    headers = {'Content-Type':'application/json'}
    headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    return get_data("{}/instances".format(orthanc_uri), headers=headers)

def fetchOrthancInstances(instance_id, remote_orthanc_uri=ORTHANC_URI, local_orthanc_uri="http://localhost:8042"):
    LOGGER.debug(f"fetchOrthancInstances called with args: {instance_id},\
         remote_orthanc_uri {remote_orthanc_uri} local_orthanc_uri {local_orthanc_uri}")
    headers = get_http_auth_header(HTTP_USER, HTTP_PASSWORD)
    content, _ = get_data("{}/instances/{}/file".format(remote_orthanc_uri, instance_id), headers=headers)
    post_data("{}/instances".format(local_orthanc_uri), content, headers)


def getInstancesOfOrthancResource(resource):
    """
    :param param1: dict as returned by orthanc/tools/find, contains infos on resource
    :returns: list of orthanc instance ID of the resource
    """
    LOGGER.debug(f"getInstancesOfOrthancResource called with args {resource}")
    instance_list = []
    try:
        resource_type = resource["Type"]
    except KeyError:
        #raise ValueError("Resource does not contain ID or Type ({})".format(resource))
        return instance_list
    if resource_type == "Patient":
        for study_id in resource["Studies"]:
            study_resource, _ = getOrthancResource("Study", study_id)
            instance_list = getInstancesOfOrthancResource(study_resource)
    elif resource_type == "Study":
        for series_id in resource["Series"]:
            series_resource, _ = getOrthancResource("Series", series_id)
            instance_list = getInstancesOfOrthancResource(series_resource)
    elif resource_type == "Series":
        instance_list.extend(resource["Instances"])
        return instance_list
    else:
        raise ValueError("Resource has unknown Type '{}'".format(resource_type))
    return instance_list

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        body = json.dumps({"Resources": [resource], "Asynchronous": True})
        #body["Asynchronous"] = "true"
        print("body is " + body)
        LOGGER.debug(f"Uploading instance {resource} to peer {PEER_NAME}")
        result = orthanc.RestApiPost("/peers/{}/store".format(PEER_NAME), body)

def OnFind(output, uri_path, **kwargs):
    LOGGER.debug(f"/enhancequery called with args: {kwargs['body']}")
    body = json.loads(kwargs["body"])
    url = '{}/tools/find'.format(ORTHANC_URI)
    post_body = {
            "Level": body["0008,0052"],
            "Expand": True,
            "Limit": 5,
            "Query": {"PatientID": body["0010,0020"], "PatientName": body["0010,0010"]}}
    post_body = json.dumps(post_body)
    headers = {"Content-Type": "application/json"}
    headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    response, _ = post_data(url, post_body, headers)
    LOGGER.debug(f"post_data response is {response}")
    remote_instances = []
    for resource in response:
        remote_instances.extend(getInstancesOfOrthancResource(resource))
    local_instances, _ = getOrthancInstances(orthanc_uri="http://localhost:8042")
    LOGGER.debug(f"local_instances are {local_instances}")
    required_instances = set(remote_instances) - set(local_instances)
    LOGGER.debug(f"required_instances are {required_instances}")
    for instance in remote_instances:
        fetchOrthancInstances(instance)
    output.AnswerBuffer('{}', 'application/json')


def get_data_debug(output, uri_path, **kwargs):
    url = 'http://localhost:8042/instances'
    headers = {'Content-Type':'application/json'}
    headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    LOGGER.debug(f"get_data called with args: {url} and headers {headers}")
    req = Request(url, headers=headers)
    resp = urlopen(req)
    if "Content-Type" in headers.keys() and headers["Content-Type"] == "application/json":
        answer_content = json.loads(resp.read().decode())
        answer_headers = resp.getheaders()
        LOGGER.debug(f"get_data got response with headers: {answer_headers}")
        return answer_content, answer_headers
    return resp.read(), resp.getheaders()




orthanc.RegisterRestCallback('/enhancequery', OnFind)
orthanc.RegisterRestCallback('/debugme', get_data_debug)
orthanc.RegisterOnChangeCallback(OnChange)





resource1 = {
      "ID" : "42edd247-21a561e5-f27fc362-81eaf1f4-12cf010d",
      "IsStable" : False,
      "LastUpdate" : "20200502T172541",
      "MainDicomTags" : {
         "PatientBirthDate" : "1998715",
         "PatientID" : "11788770005213",
         "PatientName" : "PATIENT B"
      },
      "Studies" : ["22f6c501-e9dcd8c2-52c77194-5c6a9376-b3823f5b"],
      "Type" : "Patient"
   }



#print(getInstancesOfOrthancResource(resource1))
