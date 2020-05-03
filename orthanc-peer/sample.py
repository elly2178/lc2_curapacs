import orthanc
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PEER_NAME = "c0100-orthanc"
PEER_DOMAIN = "curapacs.ch"
HTTP_USER = "orthanc"
HTTP_PASSWORD = "orthanc"

def post_data(url, data, headers={'Content-Type':'application/json'}):
    bindata = data if type(data) == bytes else data.encode('utf-8')
    req = Request(url, bindata, headers)
    resp = urlopen(req)
    return resp.read(), resp.getheaders()

def get_data(url, headers={'Content-Type':'application/json'}):
    req = Request(url, headers=headers)
    resp = urlopen(req)
    return resp.read(), resp.getheaders()

def get_http_auth_header(username, password):
    import base64
    b64string = base64.b64encode(bytes("{}:{}".format(username,password),encoding="utf-8"))
    return { "Authorization": "Basic {}".format(b64string.decode()) }

def getOrthancResource(resource_type, resource_id):
    if resource_type == "Patient":
        pass
    if resource_type == "Study":
        return get_data("http://{}.{}/studies/{}".format(PEER_NAME,PEER_DOMAIN,resource_id),
                headers={'Content-Type':'application/json'}.update(get_http_auth_header))
    if resource_type == "Series":
        pass
    

def getInstancesOfOrthancResource(resource):
    """
    :param param1: dict as returned by orthanc/tools/find, contains infos on resource
    :returns: list of orthanc instance ID of the resource
    """
    instance_list = []
    try:
        resource_id = resource["ID"]
        resource_type = resource["Type"]
    except KeyError:
        #raise ValueError("Resource does not contain ID or Type ({})".format(resource))
        return instance_list
    if resource_type == "Patient":
        for study in resource["Studies"]:
            study_resource = getOrthancResource(study)
    else:
        raise ValueError("Resource has unknown Type '{}'".format(resource_type))
    
    return instance_list

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        print('Uploading instance {} to peer {}'.format(resource,PEER_NAME))
        result = orthanc.RestApiPost("/peers/{}/store".format(PEER_NAME), json.dumps(resource))
        print("Result for {} was {}".format(resource,str(result)))

def OnFind(output, uri_path, **kwargs):
    print("KWARGS are: " + str(kwargs))
    body = json.loads(kwargs["body"])
    url = 'http://{}.{}/tools/find'.format(PEER_NAME, PEER_DOMAIN) 
    post_body = {
            "Level": body["0008,0052"],
            "Expand": True,
            "Limit": 5,
            "Query": {
                "PatientID": body["0010,0020"],
                "PatientName": body["0010,0010"]
                }
            }
    post_body = json.dumps(post_body)
    print("JSON BODY is: " + post_body)
    headers = {"Content-Type": "application/json"}
    headers.update(get_http_auth_header(HTTP_USER,HTTP_PASSWORD))
    response, _ = post_data(url, post_body, headers)
    print("JSON REPONSE IS: " + str(response.decode()))
    output.AnswerBuffer('{}', 'application/json')
    

orthanc.RegisterRestCallback('/enhancequery', OnFind)
orthanc.RegisterOnChangeCallback(OnChange)
#print(orthanc.GetTagName(100,100,"null"))
