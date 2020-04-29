from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
import pydicom

app = Flask(__name__)

# 4 Serialize objects 
ma = Marshmallow(app)


class Worklist():        
    
    def __init__(self, PatientID: int, PatientName: str, ScheduledProcedureStepSequence: list):
        # check if patientId contains other char exept ints
        
        
        try:
            self.PatientID = int(PatientID)
        except ValueError:
            raise ValueError('PatientID contains invalid value ---> {}'.format(PatientID))
        
        #check if pat name is longer than 30 char and if the chars are part of the alphabet
        try:
            if (len(PatientName) <= 30 and PatientName.isalpha()):
                self.PatientName = PatientName
            else:
                raise IOError
        except IOError:
            raise IOError('Patient Name must be maximum 30 Charactes long and contain only alphabetical signs ---> {}'.format(PatientName))
        
        # check if list is complete +-
        try:
            pass
            #if [0]= str():
                #self.ScheduledProcedureStepSequence = ScheduledProcedureStepSequence
            #else: 
                #raise TypeError
        except TypeError:
            raise TypeError('List fields are not corrrect --> {}'.format(ScheduledProcedureStepSequence))
    
    def inputValidationCheck(self, valueToCheck, requiredType, maxSize=None, isDate=False):
        if type(valueToCheck) is requiredType:
            return True
        else:
            raise ValueError("Value {} is not of type {}".format(str(valueToCheck),requiredType))

class WorklistSchema(ma.Schema):
    class Meta:
        fields = ('PatientID', 'PatientName', 'ScheduledProcedureStepSequence')

worklist_schema = WorklistSchema()

@app.route('/wl', methods = ['POST'])
def create_wl():
    
    PatientID = request.json['PatientID']
    PatientName = request.json['PatientName']
    ScheduledProcedureStepSequence = request.json['ScheduledProcedureStepSequence']
    try:
        worklist_created = Worklist(PatientID, PatientName, ScheduledProcedureStepSequence)
        
    except ValueError as error:
        return jsonify(str(error), 400)

    except IOError as anothererror:
        return jsonify(str(anothererror),400)

    except TypeError as aError:
        return jsonify(str(aError), 400)
    retval = worklist_schema.jsonify(worklist_created)
    return retval
    
     
if __name__ == "__main__":
    app.run(debug = True)


   