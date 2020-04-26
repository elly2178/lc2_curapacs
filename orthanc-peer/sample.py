import orthanc
import json

PEER_NAME = "orthanc-curapacs"

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        print('A new instance was uploaded: %s' % resource)
        print('Uploading instance {} to peer {}'.format(resource,PEER_NAME))
        result = orthanc.RestApiPost("/peers/orthanc-curapacs/store", json.dumps(resource))
        print("Result for {} was {}".format(resource,str(result)))

orthanc.RegisterOnChangeCallback(OnChange)
