from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
import pydicom

app = Flask(__name__)

# 4 Serialize objects 
ma = Marshmallow(app)


class Worklist():        
    # set of rules that need to be respected
    ruleset = [{ "PatientID": str, "constraints": { "maxlength": 64 } },
           { "PatientName": str, "constraints": { "maxlength": 32 } },
           { "Modality": str},
           { "AETitle": str, "constriants": {"maxlength": 16}},
           {" ProcedureStepStartDate": int},
           {" ProcedureStepStartTime": int},
           {" PhysicianName": str}]
           
    def __init__(self, PatientID: str, PatientName: str, ScheduledProcedureStepSequence: list):
        self.PatientID = PatientID
        self.PatientName = PatientName
        self.ScheduledProcedureStepSequence = ScheduledProcedureStepSequence        
        self.porperties_that_we_need_to_check = {}
        #json = {"PatientID": 55, "PatientName": 12345678}
        for key, value in { "PatientID": self.PatientID, "PatientName": self.PatientName}.items():
            for rule in Worklist.ruleset:
                if key in rule.keys():
                    self.check_value(key, value, rule[key], **rule["constraints"])   

    def check_value(self, key, value, requiredType, **kwargs):
        # chekcing for value type
        if not isinstance(value, requiredType):
            raise TypeError("Value for key {} not of type {}".format(key,str(requiredType)))
        
        for additional_constraint, additional_constraint_value in kwargs.items():
            #  
            if additional_constraint == "maxsize":
                # if pat id co --> give error back
                if value > additional_constraint_value:
                    raise ValueError("Value for key {} bigger than {}".format(key, additional_constraint_value))
            if additional_constraint == "maxlength":
                if len(value) > additional_constraint_value:
                    raise ValueError("Value for key {} longer than {}".format(key, additional_constraint_value))
            # pat name must contain chars and not numbers: if (len(PatientName) <= 30 and PatientName.isalpha())
        return True





 
class WorklistSchema(ma.Schema):
    class Meta:
        fields = ('PatientID', 'PatientName', 'ScheduledProcedureStepSequence')

worklist_schema = WorklistSchema()

@app.route('/wl', methods = ['POST'])
def create_wl():
    PatientID = request.json['PatientID']
    PatientName = request.json['PatientName']
    ScheduledProcedureStepSequence = request.json['ScheduledProcedureStepSequence']
    
    worklist_created = Worklist(PatientID, PatientName, ScheduledProcedureStepSequence)
    
    retval = worklist_schema.jsonify(worklist_created)
    return retval


                
if __name__ == "__main__":
    app.run(debug = True)  