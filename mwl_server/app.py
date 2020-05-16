import re
import random
import time
import os
import hashlib
import logging
import sys
import copy
from json import loads, dumps
from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from pydicom.datadict import dictionary_VR, keyword_for_tag

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[logging_handler], level=logging.DEBUG, format=LOG_FORMAT)
LOGGER = logging.getLogger()

try:
    import orthanc
except ImportError:
    LOGGER.warning("Failed to import orthanc module.")

class Worklist():
    modality_worklist_path = os.environ.get("ORTHANC_WORKLIST_DIR", "/tmp")
    modality_worklist_suffix = os.environ.get("ORTHANC_WORKLIST_SUFFIX", "wl")
    
    # set of rules that need to be respected
    ruleset = [{"PatientID": str, "constraints": {"maxlength": 64, "returnkeytype": 1 }},
               {"PatientName": str, "constraints": {"maxlength": 32, "isextendedalpha": True, "returnkeytype": 1 }},
               {"Modality": str, "constraints": {"returnkeytype": 1 }},
               {"ScheduledStationAETitle": str, "constraints": {"maxlength": 16, "returnkeytype": 1 }},
               {"ScheduledProcedureStepStartDate": str, "constraints": {"exactlength": 8, "isnumeric": True, "returnkeytype": 1}},
               {"ScheduledProcedureStepStartTime": str, "constraints": {"returnkeytype": 1}},
               {"ScheduledPerformingPhysicianName": str, "constraints": {"isextendedalpha": True, "returnkeytype": 2}}]


    def __init__(self, json=None):
        self.pydicom_dataset = Dataset()
        if json:
            self.json = loads(json)

    def create_worklist_from_json(self, json: dict):
        """
        A worklist is created using a json structure. This file contains the data
        of the Patient, de modality,accession number and can be modified as much as desired.
        First, the method checks if all the tags are present and if the rules of 
        the tags are correct. Finally, the dataset gets written to disk. 

        :param json: referes to the json file that will be created. Type: dictonary 
        :returns: sha1 hash of filename created
        """
        for key, value in Worklist.flattenIterable(json):
            for rule in Worklist.ruleset:
                if key in rule.keys():
                    self.check_value(key, value, rule[key], **rule["constraints"])
                    break
        self.check_required_tags()
        self.createDataSetFromJson()
        filehash = self.storeDataSetOnDisk()
        return {"id": filehash}

    @staticmethod
    def flattenIterable(someiterable):
        """
        Unpacks lists, dictionaries and stores all the Data from them in a temporary List.
        With each itteration, the list gets appended. 

        :param someiterable: any element type
        :returns: list of elementws"""
        flattened_list = []
        if isinstance(someiterable, list):
            for item in someiterable:
                flattened_list.extend(Worklist.flattenIterable(item))
        elif isinstance(someiterable, dict):
            for key, value in someiterable.items():
                if isinstance(value, dict):
                    flattened_list.extend(Worklist.flattenIterable(value))
                elif isinstance(value, list):
                    flattened_list.extend(Worklist.flattenIterable(value))
                else:
                    flattened_list.append((key, value))
        return flattened_list

    def replace_tags_with_keywords(self, worklist_dict):
        """
        dont ask, just enjoy
        iterate through json structure containing information on existing worklists
        and replace all occurrences of dicom tags with their corresponding keywords.

        :param worklist_dict: dictonary that contains the worklist elements
        """
        keyword_dict = copy.deepcopy(worklist_dict)
        for key, value in worklist_dict.items():
            if isinstance(value, dict):
                for dicom_tag, vr_dict in value.items():
                    dicom_keyword = keyword_for_tag(int(dicom_tag, 16))
                    keyword_dict[key][dicom_keyword] = keyword_dict[key].pop(dicom_tag)
                    if vr_dict["Value"] and isinstance(vr_dict["Value"][0], dict):
                        for index, nested_vr_dict in enumerate(vr_dict["Value"]):
                            for nested_dicom_tag, nested_nested_vr_dict in nested_vr_dict.items():
                                try:
                                    nested_dicom_keyword = keyword_for_tag(int(nested_dicom_tag, 16))
                                except ValueError:
                                    continue
                                keyword_dict[key][dicom_keyword]["Value"][index][nested_dicom_keyword] = \
                                    keyword_dict[key][dicom_keyword]["Value"][index].pop(nested_dicom_tag)
        return keyword_dict

    def create_available_worklists_response_dict(self):
        """
        Method creates a list of all the available worklists. 
        :returns: serialize obj to a Json formatted string uding conversion table 
        """
        response_dict = {}
        for worklist_filename in self.get_current_worklists():
            hashed_filename = self.hashme(worklist_filename)
            ds = self.create_dataset_from_file(Worklist.modality_worklist_path + "/" + worklist_filename)
            response_dict[hashed_filename] = ds.to_json_dict()
            response_dict = self.replace_tags_with_keywords(response_dict)
        return dumps(response_dict)

    def create_dataset_from_file(self, filepath):
        LOGGER.debug(f"Creating new pydicom dataset from file {filepath}")
        return dcmread(filepath, stop_before_pixels=True)

    def hashme(self, string_to_hash):
        LOGGER.debug(f"Worklist from file {string_to_hash} has been hashed")
        hashed_code = hashlib.sha1(string_to_hash.encode("utf-8")).hexdigest()
        return hashed_code

    def get_current_worklists(self):
        """
        Gets the worklists that are locally stored. Puts them in a temporary list. Targets
        only the files with a specific suffix

        :returns: the temporary list that contains """
        modality_worklist_dir_files = os.scandir(Worklist.modality_worklist_path)
        worklist_list = []
        with modality_worklist_dir_files as existing_files:
            for file in existing_files:
                if file.name.endswith(Worklist.modality_worklist_suffix):
                    worklist_list.append(file.name)
        LOGGER.debug("Current worklists found on disk are: " + ", ".join(worklist_list))
        return worklist_list

    def check_value(self, key, value, requiredType, **kwargs):
        """
        Checks if value meets some important requirements, e.g. typecheck and additional constraints.

        :param key: key for DICOM tag as found in JSON structure from request we received.
        :param value: Value provided for key.
        :param requiredType: Type as required by Worklist.ruleset for this key.
        :param kwargs: Set of additional constraints which need to be met by value.
        :returns: this is a description of what is returned.
        :raises TypeError: Type of value does not match requiredType.
        :raises ValueError: If additionals constraints are not met.
        """
        if not isinstance(value, requiredType):
            raise TypeError("Value for key {} not of type {}".format(key,str(requiredType)))
        
        for additional_constraint, additional_constraint_value in kwargs.items():         
            if additional_constraint == "maxsize":                # if pat id co --> give error back
                if value > additional_constraint_value:
                    raise ValueError("Value for key {} bigger than {}".format(key, additional_constraint_value))
            if additional_constraint == "maxlength":
                # if given lenght is bigger than the one deifined, raise ValErr
                if len(value) > additional_constraint_value:
                    raise ValueError("Value for key {} longer than {}".format(key, additional_constraint_value))
            if additional_constraint == "exactlength":
                if not len(value) == additional_constraint_value:
                    raise ValueError("Value for key {} is not exactly {} digits long.".format(key,additional_constraint_value))
            if additional_constraint == "isnumeric":
                if not value.isnumeric():
                   raise ValueError("Value for key {} contains non numeric characters".format(key)) 
            # remake this, it exculdes space in the name --> always err
            if additional_constraint == "isextendedalpha":
                match_pattern = r'^[a-zA-Z^ .]*$'
                match = re.match(match_pattern, value)
                if not match:
                   raise ValueError("Value for key {} does not match pattern {}".format(key, match_pattern))
        return True
     
    def createDataSetFromJson(self):
        """creates self.pydicom_dataset from self.json"""
        self.pydicom_dataset = Dataset.from_json(self.reformatJSON(self.json))
        meta_dataset = Dataset()
        meta_dataset.MediaStorageSOPClassUID = "1.2.276.0.7230010.3.1.0.1"
        meta_dataset.ImplementationClassUID = "1.2.276.0.7230010.3.0.3.6.4"
        meta_dataset.ImplementationVersionName = "CURAPACS"
        self.pydicom_dataset.file_meta = meta_dataset
        self.pydicom_dataset.preamble = b"\0" * 128
        self.pydicom_dataset.is_little_endian = True
        self.pydicom_dataset.is_implicit_VR = False
        self.pydicom_dataset.AccessionNumber = self.generateAccessionNumber()
        self.pydicom_dataset.StudyID = self.generateStudyID()

    def reformatJSON(self, request_json: dict):
        """
        iterate over key/values in json
        {"00080005": {"Value": ["ISO_IR 100"], "vr": "CS"}
        pydicom.datadict.dictionary_VR(tag)
        """
        pydicom_json = {}
        for key, value in request_json.items():
            if isinstance(value, list):
                scheduledsequences = []
                for item in value:
                    scheduledsequences.append(self.reformatJSON(item))
                pydicom_json[key] = {"Value": scheduledsequences, "vr": dictionary_VR(key)}
            else:
                pydicom_json[key] = {"Value": [value], "vr": dictionary_VR(key)}
        return pydicom_json

    def check_required_tags(self):
        """
        Verifies if all the required json keys are present and 
        respects all the given constraints
        
        :returns: True if all the constraints are correct """
        json_keys = [json_tuple[0] for json_tuple in Worklist.flattenIterable(self.json)]
        LOGGER.debug(f"json_keys are {json_keys}")
        for rule in Worklist.ruleset:
            returnkeytype = rule["constraints"].get("returnkeytype", 3)
            for key in rule.keys():
                if key == "constraints":
                    continue
                if key not in json_keys and returnkeytype in (1, 2):
                    raise KeyError(f"Required DICOM tag \"{key}\" not found in json structure.")
        return True
                      
    def storeDataSetOnDisk(self):
        """writes Dataset (Worklist DICOM File) to disk, filename is a timestamp"""
        currentDate = time.strftime('%G-%m-%d_%H-%M-%S', time.localtime())
        filename = currentDate + "." + Worklist.modality_worklist_suffix
        concatination_file_name = os.path.join(Worklist.modality_worklist_path, filename)
        self.pydicom_dataset.save_as(concatination_file_name)
        return self.hashme(filename)

    def generateAccessionNumber(self,minlength=8):
        return str(random.randint(10**minlength,10**16-1))

    def generateStudyID(self):
        return generate_uid()
    
    def http_delete(self, hashed_code: str):
        """ 
        Delete the desired Worklist with the hash hashed_code

        :param hashed_code: str hashed information of the worklist to be deleted 
        """
        # get the list of existing worklists
        # compare hashed_code local to given hashed_code for each element in worklists
        for filename_of_exsisting_worklist in self.get_current_worklists():
            if self.hashme(filename_of_exsisting_worklist) == hashed_code:
                os.remove(os.path.join(Worklist.modality_worklist_path, filename_of_exsisting_worklist))
                break
        else:
            LOGGER.error(f"User ordered deletion of non existing worklist (hash {hashed_code})")
            raise FileNotFoundError(f"The worklist corresponding to hash {hashed_code} does not exist.")
        
        return hashed_code

      
if __name__ == "__main__":
    json1 = {
    "PatientID": "11788770005213",
    "PatientName": "Armon",
    "ScheduledProcedureStepSequence": [
    {
    "Modality": "US",
    "ScheduledStationAETitle": "PhillipsUS01",
    "ScheduledProcedureStepStartDate": "20200427",
    "ScheduledProcedureStepStartTime": "100000",
    "ScheduledPerformingPhysicianName": "Max^Messermann"    
    },
    {
    "Modality": "US",
    "ScheduledStationAETitle": "PhillipsUS01",
    "ScheduledProcedureStepStartDate": "20200429",
    "ScheduledProcedureStepStartTime": "121650",
    "ScheduledPerformingPhysicianName": "Max^Messermann"
    }]
    }
    someworklist = Worklist(dumps(json1))
    print(someworklist.create_available_worklists_response_dict())


def worklist_worker(output, uri_path, **kwargs):
    """
    Uses methods GET, POST as a response to the server/ user.
    With Delete, allows a worklist to be deleted
    :param output: 
    :param **kwargs: key word argumants 
    """
    print("KWARGS : " + str(kwargs))
    if kwargs["method"] == "GET":
        myworklist = Worklist()
        worklists = myworklist.create_available_worklists_response_dict()
        output.AnswerBuffer(str(worklists), 'application/json')
    elif kwargs["method"] == "POST":
        myworklist = Worklist(json=kwargs["body"])
        response_dict = myworklist.create_worklist_from_json(myworklist.json)
        output.AnswerBuffer(str(response_dict), 'application/json')
    elif kwargs["method"] == "DELETE":
        try:
            hashed_id_of_worklist = kwargs['groups'][0]
            print(hashed_id_of_worklist)
        except IndexError:
            LOGGER.error("Hashed Nr for Worklist to delete not given")
            raise
        myworklist = Worklist()
        try:
            myworklist.http_delete(hashed_id_of_worklist)
        except FileNotFoundError as error:        
            output.SendHttpStatus(400, f"{error}", len(str(error)))
            return
        output.AnswerBuffer("{}", 'application/json')


orthanc.RegisterRestCallback('/worklists', worklist_worker)
orthanc.RegisterRestCallback('/worklists/(.*)', worklist_worker)