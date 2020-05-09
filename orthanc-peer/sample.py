import json
import base64
import sys
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import orthanc


LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[logging_handler], level=logging.DEBUG, format=LOG_FORMAT)
LOGGER = logging.getLogger()

PEER_NAME = "c0100-orthanc"
PEER_DOMAIN = "curapacs.ch"
LOCAL_HTTP_PORT = 8042
ORTHANC_URI = "http://c0100-orthanc.curapacs.ch"
HTTP_TIMEOUT = 5
HTTP_USER = "orthanc"
HTTP_PASSWORD = "orthanc"

def post_data(url, data, headers=None, timeout=HTTP_TIMEOUT, is_json=True):
    LOGGER.debug(f"post_data called with args: {url} and headers {headers}")
    if HTTP_USER:
        headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    if is_json:
        headers.update({"Content-Type": "application/json"})
    bindata = data if isinstance(data, bytes) else data.encode('utf-8')
    req = Request(url, bindata, headers)
    resp = urlopen(req, timeout=timeout)
    return json.loads(resp.read().decode()), resp.getheaders()

def get_data(url, headers=None, timeout=HTTP_TIMEOUT, is_json=True):
    """
    Issues http GET to a url
    """
    LOGGER.debug(f"get_data called with args: {url} and headers {headers}")
    if not headers:
        headers = {}
    if HTTP_USER:
        headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    if is_json:
        headers.update({"Content-Type": "application/json"})
    req = Request(url, headers=headers)
    resp = urlopen(req, timeout=timeout)
    answer_headers = resp.getheaders()
    if "Content-Type" in headers.keys() and "application/json" in headers["Content-Type"]:
        answer_content = json.loads(resp.read().decode())
        LOGGER.debug(f"get_data got json response with headers: {answer_headers}")
        return answer_content, answer_headers
    LOGGER.debug(f"get_data got response with headers: {answer_headers}")
    return resp.read(), resp.getheaders()

def get_http_auth_header(username, password):
    """
    :param username: Basic Auth Username
    :param password: Basic Auth Password
    :returns: HTTP Header as dict containing basic auth information
    """
    b64string = base64.b64encode(bytes("{}:{}".format(username, password), encoding="utf-8"))
    return {"Authorization": "Basic {}".format(b64string.decode())}

def getOrthancResource(resource_type, resource_id, orthanc_uri=ORTHANC_URI):
    """
    Given the Orthanc ID of a resource (Study/Series), return a resource dict
    containing metadata including child resources
    
    :param resource_type: "Study" or "Series"
    :param resource_id: Orthanc ID of resource
    :returns: dict containing metadata (including IDs of child resources) of resource
    """
    LOGGER.debug(f"getOrthancResource called with args: resource_type: {resource_type}, " + \
                "resource_id: {resource_id}, orthanc_uri: {orthanc_uri}")
    headers = {'Content-Type':'application/json'}
    headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    if resource_type == "Study":
        return get_data("{}/studies/{}".format(orthanc_uri, resource_id), headers=headers)
    elif resource_type == "Series":
        return get_data("{}/series/{}".format(orthanc_uri, resource_id), headers=headers)

def getOrthancInstances(orthanc_uri=ORTHANC_URI):
    """
    Ask remote orthanc API for a complete list of all available instance IDs.

    :param orthanc_uri: URI (https://sample.orthanc.org:8080) 
    """
    LOGGER.debug(f"getOrthancInstances called with args: orthanc_uri {orthanc_uri}")
    return get_data("{}/instances".format(orthanc_uri))

def fetchOrthancInstances(instance_id, remote_orthanc_uri=ORTHANC_URI,\
                        local_orthanc_uri="http://localhost:{}".format(str(LOCAL_HTTP_PORT))):
    """
    Download DICOM Data of instance with instance_id to local orthanc.

    :param instance_id: Orthanc instance id string
    :param remote_orthanc_uri: URI (https://sample.orthanc.org:8080) to fetch instances from
    :param local_orthanc_uri: URI of the instance running this plugin
    """
    LOGGER.debug(f"fetchOrthancInstances called with args: {instance_id},\
         remote_orthanc_uri {remote_orthanc_uri} local_orthanc_uri {local_orthanc_uri}")
    headers = get_http_auth_header(HTTP_USER, HTTP_PASSWORD)
    content, _ = get_data("{}/instances/{}/file".format(remote_orthanc_uri, instance_id))
    post_data("{}/instances".format(local_orthanc_uri), content, headers)


def getInstancesOfOrthancResource(resource):
    """
    Recurse downwards (Patient -> Study -> Series -> Instance) returning all instances.

    :param param1: dict as returned by orthanc/tools/find, contains infos on resource
    :returns: list of orthanc instance IDs of the resource
    """
    LOGGER.debug(f"getInstancesOfOrthancResource called with args {resource}")
    instance_list = []
    try:
        resource_type = resource["Type"]
    except KeyError:
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
    local_instances, _ = getOrthancInstances(orthanc_uri="http://localhost:{}".format(str(LOCAL_HTTP_PORT)))
    LOGGER.debug(f"local_instances are {local_instances}")
    required_instances = set(remote_instances) - set(local_instances)
    LOGGER.debug(f"Required instances not present on this orthanc are: {required_instances}")
    for instance in remote_instances:
        fetchOrthancInstances(instance)
    output.AnswerBuffer('{}', 'application/json')


"""
Retrieve Level Patient
(0010,0010) PatientName
(0010,0020) PatientID
(0010,0021) IssuerOfPatientID
(0010,0030) PatientBirthDate
(0010,0032) PatientBirthTime
(0010,0040) PatientSex
(0010,1000) OtherPatientIDs (retired)
(0010,1001) OtherPatientNames
(0010,2160) EthnicGroup
(0010,4000) PatientComments

Retrieve Level Study
(0008,0020) StudyDate
(0008,0030) StudyTime
(0008,0050) AccessionNumber
(0008,0090) ReferringPhysicianName
(0008,1030) StudyDescription
(0008,1060) NameOfPhysiciansReadingStudy
(0008,1080) AdmittingDiagnosesDescription
(0010,1010) PatientAge
(0010,1020) PatientSize
(0010,1030) PatientWeight
(0010,2180) Occupation
(0010,21B0) AdditionalPatientHistory
(0020,000D) StudyInstanceUID
(0020,0010) StudyID
(0020,1070) RETIRED_OtherStudyNumbers

Retrieve Level Series
(0008,0060) Modality
(0020,000E) SeriesInstanceUID
(0020,0011) SeriesNumber

Retrieve Level Image
(0008,0018) SOPInstanceUID
(0020,0013) InstanceNumber
"""


def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        body = json.dumps({"Resources": [resource], "Asynchronous": True})
        LOGGER.debug(f"Change Callback started, type: {changeType}, body: {body}")
        LOGGER.debug(f"Uploading instance {resource} to peer {PEER_NAME}")
        result = orthanc.RestApiPost("/peers/{}/store".format(PEER_NAME), body)


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
#orthanc.RegisterRestCallback('/debugme', get_data_debug)
orthanc.RegisterOnChangeCallback(OnChange)
print(dir(orthanc.ChangeType))

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
