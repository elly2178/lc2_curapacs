from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
import pydicom
from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.uid import UID, generate_uid
from pydicom.datadict import dictionary_VR
import re
import random
import time
import os
import hashlib
import logging
import sys

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[logging_handler], level = logging.DEBUG, format= LOG_FORMAT)
LOGGER = logging.getLogger()

class Worklist():        
    modality_worklist_path = os.environ.get("ORTHANC_WORKLIST_DIR", "/tmp")
    modality_worklist_suffix = os.environ.get("ORTHANC_WORKLIST_SUFFIX", "wl")
    
    # set of rules that need to be respected
    ruleset =  [{ "PatientID": str, "constraints": { "maxlength": 64, "returnkeytype": 1 }},
                { "PatientName": str, "constraints": { "maxlength": 32, "isextendedalpha": True, "returnkeytype": 1 }},
                { "Modality": str, "constraints": {"returnkeytype": 1 }},
                { "ScheduledStationAETitle": str, "constraints": {"maxlength": 16, "returnkeytype": 1 }},
                { "ScheduledProcedureStepStartDate": str, "constraints": {"exactlength": 8, "isnumeric": True, "returnkeytype": 1}},
                { "ScheduledProcedureStepStartTime": str, "constraints": {"returnkeytype": 1}},
                { "ScheduledPerformingPhysicianName": str, "constraints": {"isextendedalpha": True, "returnkeytype": 2}}]


    def __init__(self, json: dict):
        self.pydicom_dataset = Dataset()
        self.json = json
        self.PatientID = json["PatientID"]
        self.PatientName = json["PatientName"]
        self.ScheduledProcedureStepSequence = json["ScheduledProcedureStepSequence"]
        for key, value in Worklist.flattenIterable(json):
            for rule in Worklist.ruleset:
                if key in rule.keys():
                    self.check_value(key, value, rule[key], **rule["constraints"]) 
                    break
        self.check_required_tags()
        self.createDataSetFromJson()
        self.storeDataSetOnDisk()

    @staticmethod
    def flattenIterable(someiterable):
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

    def create_worklists_response_dict(self):
        response_dict = {}
        for worklist_filename in self.get_current_worklists():
            hashed_filename = self.hashme(worklist_filename)
            ds = self.create_dataset_from_file(Worklist.modality_worklist_path + "/" + worklist_filename)
            response_dict[hashed_filename] = ds.to_json_dict()
        return response_dict

    def create_dataset_from_file(self, filepath):
        LOGGER.debug(f"Creating new pydicom dataset from file {filepath}")
        return dcmread(filepath,stop_before_pixels=True)

    def hashme(self, string_to_hash):
        LOGGER.debug(f"Worklist from file {string_to_hash} has been hashed")
        return hashlib.sha1(string_to_hash.encode("utf-8")).hexdigest()

    def get_current_worklists(self):
        # os.scandir --> scanns all the files in a directory
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
            if isinstance(value,list):
                scheduledsequences = []
                for item in value:
                    scheduledsequences.append(self.reformatJSON(item))
                pydicom_json[key] = {"Value": scheduledsequences, "vr": dictionary_VR(key)}
            else:                                 
                pydicom_json[key] = {"Value": [value], "vr": dictionary_VR(key)}
        return pydicom_json

    def check_required_tags(self):
        """checks if all required json keys are present as defined by Worklist.ruleset --> constraints"""
        json_keys = [json_tuple[0] for json_tuple in Worklist.flattenIterable(self.json)]
        for rule in Worklist.ruleset:
            returnkeytype = rule["constraints"].get("returnkeytype",3)
            for key in rule.keys():
                if key == "constraints":
                    continue
                if key not in json_keys and returnkeytype in (1,2):
                    raise KeyError(f"Required DICOM tag \"{key}\" not found in json structure.")
        return True
                      
    def storeDataSetOnDisk(self):
        """writes Dataset (Worklist DICOM File) to disk, filename is a timestamp"""
        currentDate = time.strftime('%G-%m-%d_%H-%M-%S', time.localtime())
        concatination_file_name = os.path.join(Worklist.modality_worklist_path, currentDate + "." + Worklist.modality_worklist_suffix)
        self.pydicom_dataset.save_as(concatination_file_name)        

    def generateAccessionNumber(self,minlength=8):
        return str(random.randint(10**minlength,10**16-1))

    def generateStudyID(self):
        return generate_uid()
     
# 2.5 How to create a worklist file  use pydicom and not dcmdump
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
    someworklist = Worklist(json1)
    print(someworklist.create_worklists_response_dict())
    