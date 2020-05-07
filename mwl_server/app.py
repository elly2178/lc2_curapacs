from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.uid import UID, generate_uid
from pydicom.datadict import dictionary_VR
import re
import random
import time
import os

app = Flask(__name__)

# 4 Serialize objects 
ma = Marshmallow(app)

class Worklist():        
    #path and suffix for file
    modality_worklist_path = "/home/schumi/lc2/lc2_curapacs/mwl_server/"
    modality_worklist_suffix = "wl"
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

    # method for going through all elements of the wl and return them as tuples (key / value) of a list
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
    
    # input validation
    def check_value(self, key, value, requiredType, **kwargs):
        # chekcing for value type
        if not isinstance(value, requiredType):
            raise TypeError("Value for key {} not of type {}".format(key,str(requiredType)))
        
        for additional_constraint, additional_constraint_value in kwargs.items():         
            #  unsuded, but might be used in case of int conparas :)
            if additional_constraint == "maxsize":
                # if pat id co --> give error back
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
        """---"""
        self.pydicom_dataset = Dataset.from_json(self.reformatJSON(self.json))
        self.pydicom_dataset.is_little_endian = False
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
        currentDate = time.strftime('%G-%m-%d_%H-%M-%S', time.localtime())
        concatination_file_name = os.path.join(Worklist.modality_worklist_path, currentDate + "." + Worklist.modality_worklist_suffix)
        self.pydicom_dataset.save_as(concatination_file_name)
        

    def generateAccessionNumber(self,minlength=8):
        return str(random.randint(10**minlength,10**16-1))

    def generateStudyID(self):
        return generate_uid()
     
class WorklistSchema(ma.Schema):
    class Meta:
        fields = ('PatientID', 'PatientName', 'ScheduledProcedureStepSequence')

worklist_schema = WorklistSchema()
worklists_schema = WorklistSchema()

@app.route('/wl', methods = ['POST'])
def create_wl():
    try:
        worklist_created = Worklist(request.json)
    except ValueError as msg:
        return "Error: {}".format(msg), 400

    retval = worklist_schema.jsonify(worklist_created)  
    return retval

@app.route('/wl', methods = ['GET'])
def retrieveWorkList():
    pass
    #expected a list of all the existing workmodalities
    # expected place to look for information is in the Databanse ./worklistsdatabase --> orthanc book tutorial
    # make " ./WorklistsDatabase" a variable
    
#@app.route('/wl/updateworklist', methods = ['PUT'])                 

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
    
    #app.run(debug= True)