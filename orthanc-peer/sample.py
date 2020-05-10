import json
import base64
import sys
import logging
import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[logging_handler], level=logging.DEBUG, format=LOG_FORMAT)
LOGGER = logging.getLogger()

try:
    import orthanc
except ImportError:
    LOGGER.warning("Failed to import orthanc module.")

PEER_NAME = "c0100-orthanc"
PEER_DOMAIN = "curapacs.ch"
LOCAL_HTTP_PORT = 8042
ORTHANC_URI = "http://c0100-orthanc.curapacs.ch"
HTTP_TIMEOUT = 5
HTTP_USER = "orthanc"
HTTP_PASSWORD = "orthanc"

def post_data(url, data, headers=None, timeout=HTTP_TIMEOUT, is_json=True):
    """
    Issues http POST to a url
    """
    LOGGER.debug(f"post_data called with args: {url}, headers: {headers}, body with size: {len(data)}")
    if headers is None:
        headers = {}
    if HTTP_USER:
        headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    if is_json:
        headers.update({"Content-Type": "application/json"})
        response = requests.post(url, json=data, headers=headers, timeout=HTTP_TIMEOUT)
        return response.json(), response.headers
    else:
        response = requests.post(url, data=data, headers=headers, timeout=HTTP_TIMEOUT)
        return response.content, response.headers

def get_data(url, headers=None, timeout=HTTP_TIMEOUT):
    """
    Issues http GET to a url
    """
    if not headers:
        headers = {}
    if HTTP_USER:
        headers.update(get_http_auth_header(HTTP_USER, HTTP_PASSWORD))
    headers.update({"Accept":"application/json"})
    response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
    if response.status_code > 299:
        LOGGER.warning(f"HTTP GET got bad response, status {response.status_code}, content {response.content}")
    elif "Content-Type" in response.headers and "application/json" in response.headers["Content-Type"]:
        LOGGER.debug("HTTP GET received JSON structure.")
        return response.json(), response.headers
    else:
        LOGGER.info("HTTP GET received NON-JSON structure.")
        return response.content, response.headers

def get_http_auth_header(username, password):
    """
    :param username: Basic Auth Username
    :param password: Basic Auth Password
    :returns: HTTP Header as dict containing basic auth information
    """
    b64string = base64.b64encode(bytes("{}:{}".format(username, password), encoding="utf-8"))
    return {"Authorization": "Basic {}".format(b64string.decode())}

class Orthanc:

    def __init__(self, url, http_user=None, http_password=None, find_limit=25):
        self.url = url
        self.http_user = http_user
        self.http_password = http_password
        self.find_limit = find_limit

    def getOrthancResource(self, resource_type, resource_id, orthanc_uri=ORTHANC_URI):
        """
        Given the Orthanc ID of a resource (Study/Series), return a resource dict
        containing metadata (including child resources) of resource
        
        :param resource_type: "Study" or "Series"
        :param resource_id: Orthanc ID of resource
        :returns: dict containing metadata (including IDs of child resources) of resource
        """
        LOGGER.debug(f"getOrthancResource called with args: resource_type: {resource_type}, " + \
                    "resource_id: {resource_id}, orthanc_uri: {orthanc_uri}")
        if resource_type == "Study":
            return get_data(f"{orthanc_uri}/studies/{resource_id}")
        elif resource_type == "Series":
            return get_data(f"{orthanc_uri}/series/{resource_id}")

    def getOrthancInstances(self):
        """
        Ask remote orthanc API for a complete list of all available instance IDs.

        :param orthanc_uri: URI (https://sample.orthanc.org:8080) 
        """
        instance_list, _ = get_data(f"{self.url}/instances")
        LOGGER.debug(f"local_instances are {instance_list}")
        return instance_list

    def fetchOrthancInstance(self, instance_id, remote_orthanc_uri=ORTHANC_URI):
        """
        Download DICOM Data of instance with instance_id to local orthanc.

        :param instance_id: Orthanc instance id string
        :param remote_orthanc_uri: URI (https://sample.orthanc.org:8080) to fetch instances from
        :param local_orthanc_uri: URI of the instance running this plugin
        """
        LOGGER.debug(f"Fetching instance {instance_id} from {remote_orthanc_uri}")
        content, _ = get_data(f"{remote_orthanc_uri}/instances/{instance_id}/file")
        post_data(f"{self.url}/instances", content, is_json=False)

    def getInstancesOfOrthancResource(self, resource):
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
                study_resource, _ = self.getOrthancResource("Study", study_id)
                instance_list = self.getInstancesOfOrthancResource(study_resource)
        elif resource_type == "Study":
            for series_id in resource["Series"]:
                series_resource, _ = self.getOrthancResource("Series", series_id)
                instance_list = self.getInstancesOfOrthancResource(series_resource)
        elif resource_type == "Series":
            instance_list.extend(resource["Instances"])
            return instance_list
        else:
            raise ValueError(f"Resource has unknown Type {resource_type}")
        return instance_list
    
    def findResources(self, query, level="Patient", limit=None):
        post_body = {"Level": level,
                     "Expand": True,
                     "Query": query}
        if limit is not None:
            post_body.update("limit", self.find_limit)
        content, _ = post_data(f"{self.url}/tools/find", post_body)
        LOGGER.debug(f"Resources found via /tools/find are {content}")
        return content

def OnFind(output, uri_path, **kwargs):
    LOGGER.debug(f"{uri_path} called with body: {kwargs['body']}")
    local_orthanc = Orthanc(f"http://localhost:{LOCAL_HTTP_PORT}",
                            http_user=HTTP_USER,
                            http_password=HTTP_PASSWORD)
    remote_orthanc = Orthanc(ORTHANC_URI,
                             http_user=HTTP_USER,
                             http_password=HTTP_PASSWORD)
    
    body = json.loads(kwargs["body"])
    find_level = body["0008,0052"]
    find_query = {"PatientID": body["0010,0020"], "PatientName": body["0010,0010"]}
    orthanc_resources = remote_orthanc.findResources(find_query, level=find_level)
    remote_instances = []
    for resource in orthanc_resources:
        remote_instances.extend(remote_orthanc.getInstancesOfOrthancResource(resource))
    local_instances = local_orthanc.getOrthancInstances()
    required_instances = set(remote_instances) - set(local_instances)
    LOGGER.debug(f"Required instances not present on this orthanc are: {required_instances}")
    for instance in required_instances:
        local_orthanc.fetchOrthancInstance(instance)
    if output is not None:
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

if "orthanc" in sys.modules:
    orthanc.RegisterRestCallback('/enhancequery', OnFind)
    orthanc.RegisterOnChangeCallback(OnChange)
else:
    sample_body = b'{"0008,0052":"Patient", "0010,0010":"PATIENT C", "0010,0020":""}'
    OnFind(None,"/enhancequery",body=sample_body)

