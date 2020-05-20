import json
import base64
import sys
import logging
import requests
from pydicom.datadict import keyword_for_tag, tag_for_keyword

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
        try: 
            json_response = response.json()
        except json.JSONDecodeError:
            LOGGER.error(f"Data received by post_data is malformed json structure ({response}).")
            json_response = {}
        return json_response, response.headers
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
        raise requests.ConnectionError()
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

    def getOrthancResource(self, resource_type, resource_id):
        """
        Given the Orthanc ID of a resource (Study/Series), return a resource dict
        containing metadata (including child resources) of resource
        
        :param resource_type: "Study" or "Series"
        :param resource_id: Orthanc ID of resource
        :returns: dict containing metadata (including IDs of child resources) of resource
        """
        LOGGER.debug(f"getOrthancResource called with args: resource_type: {resource_type}, " + \
                    f"resource_id: {resource_id}, orthanc_uri: {self.url}")
        if resource_type.lower() == "patient":
            query_subpath = "patients"
        elif resource_type.lower() == "study":
            query_subpath = "studies"
        elif resource_type.lower() == "series":
            query_subpath = "series"
        elif resource_type.lower() == "instance":
            query_subpath = "instances"
        else:
            raise ValueError(f"Unknown resource type requested ({resource_type})")
        try:
            content, headers = get_data(f"{self.url}/{query_subpath}/{resource_id}")
        except (requests.ConnectionError, requests.ConnectTimeout):
            LOGGER.error(f"Orthanc failed to respond to resource query.")
            content, headers = {}, {}
        return (content, headers)

    def getMainDicomTagsForOrthancResource(self, resource):
        """
        Given a resource dict grabbed from orthanc, returns a dict of its tags (numeric)
        & values describing the resource
        """
        try:
            main_dicom_tags_dict = resource["MainDicomTags"]
        except KeyError:
            LOGGER.error(f"Resource did not contain MainDicomTags: {resource}")
        for keyword in resource["MainDicomTags"].keys():
            numeric_tag = keyword_for_tag(keyword)
            main_dicom_tags_dict[numeric_tag] = main_dicom_tags_dict.pop(keyword)
        return main_dicom_tags_dict
        
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

    def getSubresourcesOfOrthancResource(self, resource: dict, level: str):
        """
        Recurse downwards (Patient -> Study -> Series -> Instance) returning all subresources
        of type level
         
        :param resource: dict as returned by orthanc/tools/find, contains infos on resource
        :param level: string as returned by getQueryRetrieveLevel
        :returns: list of dicts of orthanc resources
        """
        LOGGER.debug(f"getSubresourcesOfOrthancResource called with args {resource}, {level}")
        resource_list = []
        try:
            resource_type = resource["Type"]
        except KeyError:
            LOGGER.error(f"Key 'Type' not found in resource: {resource}")
            return resource_list
        if resource_type == "Patient":
            if level == "patient":
                return [resource]
            else:
                for study_id in resource["Studies"]:
                    study_resource, _ = self.getOrthancResource("Study", study_id)
                    resource_list.extend(self.getSubresourcesOfOrthancResource(study_resource, level))
        elif resource_type == "Study":
            if level == "study":
                return [resource]
            else:
                for series_id in resource["Series"]:
                    series_resource, _ = self.getOrthancResource("Series", series_id)
                    resource_list.extend(self.getSubresourcesOfOrthancResource(series_resource, level))
        elif resource_type == "Series":
            if level == "series":
                return [resource]
            else:
                for instance_id in resource["Instances"]:
                    instance_resource, _ = self.getOrthancResource("Instance", instance_id)
                    resource_list.extend(instance_resource)
        else:
            raise ValueError(f"Resource has unknown Type {resource_type}")
        return resource_list

    def getTagsAndValuesOfOrthancResource(self, resource_id: str, level: str):
        """
        Gets DICOM tags and their corresponding value describing an instance from Orthanc.
        The "short" parameter makes orthanc return a flat dict of tags: value representing
        all DICOM tags of the instance.

        :param instance_id: Orthanc instance id string
        :returns: dictionary, each item being a tag/value pair
        """
        try:
            if level == "patient":
                dicom_dict, _ = get_data(self.url + f"/patients/{resource_id}/shared-tags?short=True")
            elif level == "study":
                dicom_dict, _ = get_data(self.url + f"/studies/{resource_id}/shared-tags?short=True")
            elif level == "series":
                dicom_dict, _ = get_data(self.url + f"/series/{resource_id}/shared-tags?short=True")
            elif level == "instance":
                dicom_dict, _ = get_data(self.url + f"/instances/{resource_id}/tags?short=True")
            else:
                raise ValueError(f"Unknown find level {level}")
        except requests.ConnectionError:
            LOGGER.error(f"Failed to retrieve dicom resource {resource_id} from {self.url}")
            return {}
        LOGGER.debug(f"Got dicom dictionary describing resource {resource_id}: {dicom_dict.keys()}")
        return dicom_dict

    def findResources(self, query, level, limit=None):
        """
        Does a find request over the orthanc REST API (see https://api.orthanc-server.com/#tag/Find)
        
        :param query: dictionary containing query, see collateFindQuery
        :param level: corresponds to C-FIND retrieve level
        :param limit: cut off after X amount of results
        """
        post_body = {"Level": level,
                     "Expand": True,
                     "Query": query}
        if limit is not None:
            post_body.update("limit", self.find_limit)
        LOGGER.debug(f"Searching resources at level {level} and query {query}")
        content, _ = post_data(f"{self.url}/tools/find", post_body)
        LOGGER.debug(f"Query via {self.url}/tools/find found the following resources: {content}")
        return content

    def getDictFromRequestBody(self, request_body: bytes):
        """
        Reads the the POST body as sent by orthanc when calling this plugin

        :param request_body: bytestring, should contain valid json
        :returns: dictionary loaded from json
        """
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

    @staticmethod
    def getQueryRetrieveLevel(request_dict: dict):
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

    @staticmethod
    def collateFindQuery(request_dict: dict):
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
        retrieve_level = Orthanc.getQueryRetrieveLevel(request_dict).lower()
        for dicom_tag, dicom_value in request_dict.items():
            dicom_group, dicom_element = dicom_tag.split(",")
            try:
                hex_tag = int(f"{dicom_group}{dicom_element}", 16)
            except ValueError:
                LOGGER.error(f"Failed to convert dicom_group ({dicom_group}) " +\
                             f"or dicom_element ({dicom_element}) to hex value.")
                raise ValueError()
            dicom_keyword = keyword_for_tag(hex_tag)
            if dicom_keyword not in irrelevant_keywords:
                if dicom_keyword not in Orthanc.valid_keywords_for_retrieve_level[retrieve_level]:
                    LOGGER.warning(f"Find query contains invalid keyword {dicom_keyword}"+\
                                    f" for retrieve level {retrieve_level}")
                find_query[dicom_keyword] = dicom_value
        return find_query

    @staticmethod
    def filterTagsOfDicomDict(dicom_dict, find_query, find_level):
        """
        Filter out json values that cause exceptions in orthanc when
        json is converted to DICOM file.
        """
        LOGGER.debug(f"filterTagsOfDicomDict called with find_query {find_query}, find_level {find_level}")
        #remove picture data ("7fe0,0010", "0002,0002"), otherwise orthanc starts screaming
        #encoding shall be returned with every answer
        required_tags = ["0008,0005"]
        find_query_tags = [tag_for_keyword(keyword) for keyword in find_query.keys()]
        find_query_tags = [f"{tag:08X}"[:4] + "," + f"{tag:08X}"[4:] for tag in find_query_tags]
        LOGGER.debug(f"Filtering out tags from json structure not in {find_query_tags} or {required_tags}")
        #return only tags that the user asked for in the c-find query
        return_dict = {k:v for (k, v) in dicom_dict.items() if k in find_query_tags + required_tags}
        LOGGER.debug(f"Adding QueryRetrieveLevel ({find_level}) to answer.")
        return_dict["0008,0052"] = find_level.capitalize()
        return return_dict
    
    @staticmethod
    def getIDOfResource(resource: dict):
        """
        Return ID field of Orthanc resource
        """
        try:
            resource_id = resource["ID"]
        except KeyError:
            LOGGER.error(f"Failed to read ID from resource: {resource}")
            raise
        return resource_id
    
    @staticmethod
    def getResourceByID(resource_list, resource_id: str):
        """
        search for a resource identified by its ID in a list of Orthanc resources
        """
        for resource in resource_list:
            if resource["ID"] == resource_id:
                return resource
        

def enhance_query(output, uri_path, **kwargs):
    LOGGER.debug(f"{uri_path} called with body: {kwargs['body']}")
    local_orthanc = Orthanc(f"http://localhost:{LOCAL_HTTP_PORT}",
                            http_user=HTTP_USER,
                            http_password=HTTP_PASSWORD)
    remote_orthanc = Orthanc(ORTHANC_URI,
                             http_user=HTTP_USER,
                             http_password=HTTP_PASSWORD)
    
    request_body_dict = local_orthanc.getDictFromRequestBody(kwargs["body"])
    LOGGER.debug(f"Request body decoded to: {request_body_dict}")

    find_level = Orthanc.getQueryRetrieveLevel(request_body_dict)
    find_query = Orthanc.collateFindQuery(request_body_dict)

    #Search for resources via Orthanc API (remote), store all resources found in list
    try:
        remote_resources = []
        remote_orthanc_resources_found = remote_orthanc.findResources(find_query, find_level)
    except (requests.ConnectTimeout, requests.ConnectionError):
        LOGGER.error(f"Failed to connect to {remote_orthanc.url} to query for resources.")
    else:
        for resource in remote_orthanc_resources_found:
            resource_list = remote_orthanc.getSubresourcesOfOrthancResource(resource, find_level)
            LOGGER.debug(f"Resources found for remote resource: {resource_list}")
            remote_resources.extend(resource_list)
    
    #Search for resources via Orthanc API (local), store all resources found in list
    local_orthanc_resources_found = local_orthanc.findResources(find_query, find_level)
    local_resources = []
    for resource in local_orthanc_resources_found:
        resource_list = local_orthanc.getSubresourcesOfOrthancResource(resource, find_level)
        LOGGER.debug(f"Resources found for local resource: {resource_list}")
        local_resources.extend(resource_list)
    

    remote_ids = [Orthanc.getIDOfResource(resource) for resource in remote_resources]
    local_ids = [Orthanc.getIDOfResource(resource) for resource in local_resources]
    strictly_remote_ids = set(remote_ids) - set(local_ids)
    strictly_local_ids = set(local_ids) - set(remote_ids)
    intersecting_ids = set(local_ids) & set(remote_ids)
    LOGGER.debug(f"Required resources not present on local orthanc are: {strictly_remote_ids}")
    LOGGER.debug(f"Resources present on both local and remote ortanc are: {strictly_local_ids}")
    LOGGER.debug(f"Resources present on both local and remote ortanc are: {intersecting_ids}")

    #Collate dictionaries (numeric dicom tags / dicom values) for every resource found
    dicom_list = []
    try:
        for resource_id in strictly_remote_ids:
            resource = Orthanc.getResourceByID(remote_resources, resource_id)
            dicom_dict = remote_orthanc.getTagsAndValuesOfOrthancResource(resource_id, find_level)
            dicom_list.append(Orthanc.filterTagsOfDicomDict(dicom_dict, find_query, find_level))
    except (requests.ConnectTimeout, requests.ConnectionError):
        LOGGER.error(f"Failed to connect to {remote_orthanc.url} to get dicom data for instances.")

    for resource_id in strictly_local_ids | intersecting_ids:
        resource = Orthanc.getResourceByID(local_resources, resource_id)
        dicom_dict = local_orthanc.getTagsAndValuesOfOrthancResource(resource_id, find_level)
        dicom_list.append(Orthanc.filterTagsOfDicomDict(dicom_dict, find_query, find_level))

    dicom_list_as_json = json.dumps(dicom_list)
    LOGGER.debug(f"Returning list of dicom dicts to caller: {dicom_list_as_json}")

    if output is not None:
        output.AnswerBuffer(dicom_list_as_json, 'application/json')


def enhance_c_move():
    pass

def OnChange(changeType, level, resource):
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        body = json.dumps({"Resources": [resource], "Asynchronous": True})
        LOGGER.debug(f"Change Callback started, type: {changeType}, body: {body}")
        LOGGER.debug(f"Uploading instance {resource} to peer {PEER_NAME}")
        result = orthanc.RestApiPost("/peers/{}/store".format(PEER_NAME), body)
        result_dict = json.loads(result.decode())
        LOGGER.debug(f"Orthanc job with ID {result_dict['ID']} started.")

if "orthanc" in sys.modules:
    orthanc.RegisterRestCallback('/enhancequery', enhance_query)
    orthanc.RegisterOnChangeCallback(OnChange)
else:
    sample_body = b'{"0008,0052":"Patient", "0010,0010":"PATIENT C", "0010,0020":""}'
    enhance_query(None, "/enhancequery", body=sample_body)


#output methods: 'AnswerBuffer', 'CompressAndAnswerJpegImage', 'CompressAndAnswerPngImage', 'Redirect',\
#  'SendHttpStatus', 'SendHttpStatusCode', 'SendMethodNotAllowed', 'SendMultipartItem', 'SendUnauthorized',\
#  'SetCookie', 'SetHttpErrorDetails', 'SetHttpHeader', 'StartMultipartAnswer'
