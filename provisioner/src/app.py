from flask import Flask, jsonify
from helpers.listNamespaces import list_namespaces
from helpers.listOnlyPacs import list_only_Specific
from helpers.showFullObject import get_showfullobject
from helpers.versionStructuredAll import getAllVersions

app = Flask(__name__)

# global variable
__version__ = '0.1'


@app.route('/allversions', methods=['GET'])
def allversions():
    return getAllVersions()
    
@app.route('/namespaces', methods=['GET'])
def namespaces():
    return list_namespaces()

@app.route('/showfullobject', methods=['GET'])
def showfullobject():
    return get_showfullobject()

@app.route('/listenTo', methods=['GET'])
def only():
    return list_only_Specific()

@app.route('/version',methods=['GET'])
def get_version():
    return jsonify(__version__)

# run server
if __name__ == "__main__":
    app.run(debug=True)