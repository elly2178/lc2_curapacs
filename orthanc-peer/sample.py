import orthanc
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PEER_NAME = "orthanc-curapacs"

def post_data(url, data, headers={'Content-Type':'application/json'}):
    bindata = data if type(data) == bytes else data.encode('utf-8')
    req = Request(url, bindata, headers)
    resp = urlopen(req)
    return resp.read(), resp.getheaders()

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        print('A new instance was uploaded: %s' % resource)
        print('Uploading instance {} to peer {}'.format(resource,PEER_NAME))
        result = orthanc.RestApiPost("/peers/orthanc-curapacs/store", json.dumps(resource))
        print("Result for {} was {}".format(resource,str(result)))

def OnFind(output, uri_path, **kwargs):
    print("KWARGS are: " + str(kwargs))
    body = json.loads(kwargs["body"])
    print("Body is: " + str(body))
    
    url = 'http://c0100-orthanc.curapacs.ch/tools/find' 
    post_body = {
            "Level": "Study",
            "Limit": 5,
            "Query": {
                "PatientID": "*"
                }
            }
    post_body = json.dumps(post_body)
    print("JSON BODY is: " + post_body)
    headers = { "Authorization": "Basic b3J0aGFuYzpvcnRoYW5j", 
            "Content-Type": "application/json" }
    response, _ = post_data(url, post_body, headers)
    print("JSON REPONSE IS: " + str(response.decode()))
    
    output.AnswerBuffer('{}', 'application/json')
    

orthanc.RegisterRestCallback('/enhancequery', OnFind)
orthanc.RegisterOnChangeCallback(OnChange)
print(orthanc.GetTagName(100,100,"null"))
