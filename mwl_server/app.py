from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
import pydicom
import re

app = Flask(__name__)

# 4 Serialize objects 
ma = Marshmallow(app)
# big task: find meth to itterate in spsq

class Worklist():        
    # set of rules that need to be respected
    ruleset =  [{ "PatientID": str, "constraints": { "maxlength": 64} },
                { "PatientName": str, "constraints": { "maxlength": 32, "isextendedalpha": True } },
                { "Modality": str, "constraints": {} },
                { "AETitle": str, "constraints": {"maxlength": 16}},
                { "ProcedureStepStartDate": str, "constraints": {"exactlength": 8, "isnumeric": True}},
                { "ProcedureStepStartTime": str, "constraints": {} },
                { "PhysicianName": str, "constraints": {"isextendedalpha": True }}]           

    def __init__(self, json: dict):
        self.json = json
        self.PatientID = json["PatientID"]
        self.PatientName = json["PatientName"]
        self.ScheduledProcedureStepSequence = json["ScheduledProcedureStepSequence"]
        for key, value in Worklist.flattenIterable(json):
            for rule in Worklist.ruleset:
                if key in rule.keys():
                    self.check_value(key, value, rule[key], **rule["constraints"]) 
                    break 

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

class WorklistSchema(ma.Schema):
    class Meta:
        fields = ('PatientID', 'PatientName', 'ScheduledProcedureStepSequence')

worklist_schema = WorklistSchema()

@app.route('/wl', methods = ['POST'])
def create_wl():
    #PatientID = request.json['PatientID']
    #PatientName = request.json['PatientName']
    #ScheduledProcedureStepSequence = request.json['ScheduledProcedureStepSequence']
    try:
        worklist_created = Worklist(request.json)
    except ValueError as msg:
        return "Error: {}".format(msg), 400

    retval = worklist_schema.jsonify(worklist_created)  
    return retval
                 
if __name__ == "__main__":
    app.run(debug = True)  