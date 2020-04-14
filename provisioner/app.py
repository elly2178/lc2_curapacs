from flask import Flask, jsonify
from helpers.listNamespaces import list_namespaces
from helpers.listOnlyPacs import list_only_Specific

app = Flask(__name__)

# global variable
__version__ = '0.1'



@app.route('/listen', methods=['GET'])
def listen():
    return list_namespaces()

@app.route('/listenTo', methods=['GET'])
def only():
    return list_only_Specific()

@app.route('/version',methods=['GET'])
def get_version():
    return jsonify(__version__)

# run server
if __name__ == "__main__":
    app.run(debug=True)