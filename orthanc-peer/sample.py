import json
import base64
import sys
import logging
import requests
from pydicom.datadict import keyword_for_tag

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
        response = requests.post(url, json=data, headers=headers, timeout=timeout)
        return response.json(), response.headers
    else:
        response = requests.post(url, data=data, headers=headers, timeout=timeout)
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
    response = requests.get(url, headers=headers, timeout=timeout)
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

    valid_keywords_for_retrieve_level = {
        "patient": ["PatientName", "PatientID", "IssuerOfPatientID",
                    "PatientBirthDate", "PatientBirthTime", "PatientSex",
                    "OtherPatientNames", "EthnicGroup", "PatientComments"],
        "study":   ["StudyDate", "StudyTime", "AccessionNumber",
                    "ReferringPhysicianName", "StudyDescription",
                    "NameOfPhysiciansReadingStudy", "AdmittingDiagnosesDescription",
                    "PatientAge", "PatientSize", "PatientWeight", "Occupation", 
                    "AdditionalPatientHistory", "StudyInstanceUID", "StudyID"],
        "series":  ["Modality", "SeriesInstanceUID", "SeriesNumber"],
        "instance":["SOPInstanceUID", "InstanceNumber"]
    }

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

    def fetchOrthancInstance(self, instance_id: str, remote_orthanc_uri=ORTHANC_URI):
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

    def getTagsAndValuesOfOrthancInstance(self, instance_id: str):
        """
        Gets DICOM tags and their corresponding value describing an instance from Orthanc

        :param instance_id: Orthanc instance id string
        :returns: dictionary, each item being a tag/value pair
        """
        dicom_dict, _ = get_data(self.url + f"/instances/{instance_id}/tags?short=True")
        LOGGER.debug(f"Got dicom dictionary describing instance {instance_id}: {dicom_dict}")
        return dicom_dict

    def findResources(self, query, level="Patient", limit=None):
        post_body = {"Level": level,
                     "Expand": True,
                     "Query": query}
        if limit is not None:
            post_body.update("limit", self.find_limit)
        content, _ = post_data(f"{self.url}/tools/find", post_body)
        LOGGER.debug(f"Query via {self.url}/tools/find found the following resources: {content}")
        return content

    def getDictFromRequestBody(self, request_body: bytes):
        try:
            body_string = request_body.decode()
        except UnicodeDecodeError:
            LOGGER.error("Failed to decode bytes received by callback function.")
            raise
        try:
            body_dict = json.loads(body_string)
        except json.decoder.JSONDecodeError:
            LOGGER.error(f"Failed to decode JSON structure received by callback function: {body_string}")
            raise
        return body_dict

    def getQueryRetrieveLevel(self, request_dict: dict):
        """
        :param request_dict: dict containing json structure with a flat dict,
                             containing keys (dicom tag) and values (tag values)
                             with info on what is being searched by C-FIND
        :returns: String describing C-FIND retrieve level
        """
        try:
            retrieve_level = request_dict["0008,0052"].lower()
        except IndexError:
            LOGGER.error(f"Unable to determine C-FIND retrieve level from callback. request_dict: {request_dict}")
            raise
        retrieve_level = "instance" if retrieve_level == "image" else retrieve_level
        if retrieve_level not in ["patient", "study", "series", "instance"]:
            LOGGER.error(f"Unknown QueryRetrieveLevel found: {retrieve_level}")
            raise ValueError()
        return retrieve_level

    def collateFindQuery(self, request_dict: dict):
        """
        Reads request_dict and creates query dict required by findResources method.
        The resulting query can only contain tags allowed by the given retrieve level.
        Any tag not in valid_keywords_for_retrieve_level will be dropped.

        :param request_dict: dict containing json structure with a flat dict,
                             containing keys (dicom tag) and values (tag values)
                             with info on what is being searched by C-FIND
        :returns: flat dict containing query string as used by /tools/find
        """
        find_query = {}
        irrelevant_keywords = ["QueryRetrieveLevel"]
        retrieve_level = self.getQueryRetrieveLevel(request_dict).lower()
        for dicom_tag, dicom_value in request_dict.items():
            dicom_group, dicom_element = dicom_tag.split(",")
            try:
                hex_tag = int(f"{dicom_group}{dicom_element}", 16)
            except ValueError:
                LOGGER.error(f"Failed to convert dicom_group ({dicom_group}) " +\
                             f"or dicom_element ({dicom_element}) to hex value.")
                raise ValueError()
            dicom_keyword = keyword_for_tag(hex_tag)
            if dicom_keyword not in irrelevant_keywords and \
                    dicom_keyword in Orthanc.valid_keywords_for_retrieve_level[retrieve_level]:
                find_query[dicom_keyword] = dicom_value
        return find_query

        
def enhance_query(output, uri_path, **kwargs):
    LOGGER.debug(f"{uri_path} called with body: {kwargs['body']}")
    local_orthanc = Orthanc(f"http://localhost:{LOCAL_HTTP_PORT}",
                            http_user=HTTP_USER,
                            http_password=HTTP_PASSWORD)
    remote_orthanc = Orthanc(ORTHANC_URI,
                             http_user=HTTP_USER,
                             http_password=HTTP_PASSWORD)
    
    request_body_dict = local_orthanc.getDictFromRequestBody(kwargs["body"])
    LOGGER.debug(f"request body decoded to: {request_body_dict}")
    find_level = local_orthanc.getQueryRetrieveLevel(request_body_dict)
    find_query = local_orthanc.collateFindQuery(request_body_dict)

    remote_orthanc_resources_found = remote_orthanc.findResources(find_query, level=find_level)
    remote_instances = []
    for resource in remote_orthanc_resources_found:
        remote_instances.extend(remote_orthanc.getInstancesOfOrthancResource(resource))
    
    local_orthanc_resources_found = local_orthanc.findResources(find_query, level=find_level)
    local_instances = []
    for resource in local_orthanc_resources_found:
        local_instances.extend(local_orthanc.getInstancesOfOrthancResource(resource))
    
    strictly_remote_instances = set(remote_instances) - set(local_instances)
    strictly_local_instances = set(local_instances) - set(remote_instances)
    intersecting_instances = set(local_instances) & set(remote_instances)
    LOGGER.debug(f"Required instances not present on local orthanc are: {strictly_remote_instances}")

    dicom_list = []
    for instance in strictly_remote_instances:
        dicom_list.append(remote_orthanc.getTagsAndValuesOfOrthancInstance(instance))
    
    for instance in strictly_local_instances | intersecting_instances:
        dicom_list.append(local_orthanc.getTagsAndValuesOfOrthancInstance(instance))

    if output is not None:
        #output.AnswerBuffer('{"PatientID": "11788770006213"}', 'application/json')
        output.AnswerBuffer(json.dumps(dicom_list), 'application/json')
        #https://sdk.orthanc-server.com/group__Toolbox.html#ga88726ae4c968c1151a01a8a770d7b90e
        #https://sdk.orthanc-server.com/group__DicomCallbacks.html#ga71ccca51dbfa489b0e4f0899e791200c

def enhance_c_move():
    pass

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        body = json.dumps({"Resources": [resource], "Asynchronous": True})
        LOGGER.debug(f"Change Callback started, type: {changeType}, body: {body}")
        LOGGER.debug(f"Uploading instance {resource} to peer {PEER_NAME}")
        result = orthanc.RestApiPost("/peers/{}/store".format(PEER_NAME), body)

if "orthanc" in sys.modules:
    orthanc.RegisterRestCallback('/enhancequery', enhance_query)
    orthanc.RegisterOnChangeCallback(OnChange)
else:
    sample_body = b'{"0008,0052":"Patient", "0010,0010":"PATIENT C", "0010,0020":""}'
    enhance_query(None, "/enhancequery", body=sample_body)



#output methods: 'AnswerBuffer', 'CompressAndAnswerJpegImage', 'CompressAndAnswerPngImage', 'Redirect',\
#  'SendHttpStatus', 'SendHttpStatusCode', 'SendMethodNotAllowed', 'SendMultipartItem', 'SendUnauthorized',\
#  'SetCookie', 'SetHttpErrorDetails', 'SetHttpHeader', 'StartMultipartAnswer'