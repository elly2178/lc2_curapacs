import json
import requests
from pydicom.datadict import keyword_for_tag, tag_for_keyword
from curapacs_python.helpers import get_data, post_data
from curapacs_python import config



class OrthancHost:

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
        config.LOGGER.debug(f"getOrthancResource called with args: resource_type: {resource_type}, " + \
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
            config.LOGGER.error(f"Orthanc failed to respond to resource query.")
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
            config.LOGGER.error(f"Resource did not contain MainDicomTags: {resource}")
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
        config.LOGGER.debug(f"local_instances are {instance_list}")
        return instance_list

    def fetchOrthancInstance(self, instance_id: str, remote_orthanc_uri=config.ORTHANC_URI):
        """
        Download DICOM Data of instance with instance_id to local orthanc.

        :param instance_id: Orthanc instance id string
        :param remote_orthanc_uri: URI (https://sample.orthanc.org:8080) to fetch instances from
        :param local_orthanc_uri: URI of the instance running this plugin
        """
        config.LOGGER.debug(f"Fetching instance {instance_id} from {remote_orthanc_uri}")
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
        config.LOGGER.debug(f"getSubresourcesOfOrthancResource called with args {resource}, {level}")
        resource_list = []
        try:
            resource_type = resource["Type"]
        except KeyError:
            config.LOGGER.error(f"Key 'Type' not found in resource: {resource}")
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
        elif resource_type == "Instance":
            return [resource]
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
            config.LOGGER.error(f"Failed to retrieve dicom resource {resource_id} from {self.url}")
            return {}
        config.LOGGER.debug(f"Got dicom dictionary describing resource {resource_id}: {dicom_dict.keys()}")
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
        config.LOGGER.debug(f"Searching resources at level {level} and query {query}")
        content, _ = post_data(f"{self.url}/tools/find", post_body)
        config.LOGGER.debug(f"Query via {self.url}/tools/find found the following resources: {content}")
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
            config.LOGGER.error("Failed to decode bytes received by callback function.")
            raise
        try:
            body_dict = json.loads(body_string)
        except json.decoder.JSONDecodeError:
            config.LOGGER.error(f"Failed to decode JSON structure received by callback function: {body_string}")
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
            config.LOGGER.error(f"Unable to determine C-FIND retrieve level from callback. request_dict: {request_dict}")
            raise
        retrieve_level = "instance" if retrieve_level == "image" else retrieve_level
        if retrieve_level not in ["patient", "study", "series", "instance"]:
            config.LOGGER.error(f"Unknown QueryRetrieveLevel found: {retrieve_level}")
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
        retrieve_level = OrthancHost.getQueryRetrieveLevel(request_dict).lower()
        for dicom_tag, dicom_value in request_dict.items():
            dicom_group, dicom_element = dicom_tag.split(",")
            try:
                hex_tag = int(f"{dicom_group}{dicom_element}", 16)
            except ValueError:
                config.LOGGER.error(f"Failed to convert dicom_group ({dicom_group}) " +\
                             f"or dicom_element ({dicom_element}) to hex value.")
                raise ValueError()
            dicom_keyword = keyword_for_tag(hex_tag)
            if dicom_keyword not in irrelevant_keywords:
                if dicom_keyword not in OrthancHost.valid_keywords_for_retrieve_level[retrieve_level]:
                    config.LOGGER.warning(f"Find query contains invalid keyword {dicom_keyword}"+\
                                    f" for retrieve level {retrieve_level}")
                find_query[dicom_keyword] = dicom_value
        return find_query

    @staticmethod
    def filterTagsOfDicomDict(dicom_dict, find_query, find_level):
        """
        Filter out json values that cause exceptions in orthanc when
        json is converted to DICOM file.
        """
        config.LOGGER.debug(f"filterTagsOfDicomDict called with find_query {find_query}, find_level {find_level}")
        #remove picture data ("7fe0,0010", "0002,0002"), otherwise orthanc starts screaming
        #encoding shall be returned with every answer
        required_tags = ["0008,0005"]
        find_query_tags = [tag_for_keyword(keyword) for keyword in find_query.keys()]
        find_query_tags = [f"{tag:08X}"[:4] + "," + f"{tag:08X}"[4:] for tag in find_query_tags]
        config.LOGGER.debug(f"Filtering out tags from json structure not in {find_query_tags} or {required_tags}")
        #return only tags that the user asked for in the c-find query
        return_dict = {k:v for (k, v) in dicom_dict.items() if k in find_query_tags + required_tags}
        config.LOGGER.debug(f"Adding QueryRetrieveLevel ({find_level}) to answer.")
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
            config.LOGGER.error(f"Failed to read ID from resource: {resource}")
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
