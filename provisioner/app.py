from flask import Flask, jsonify

app = Flask(__name__)

# global variable
__version__ = '0.1'

@app.route('/version',methods=['GET'])
def get_version():
    return jsonify(__version__)
# run server
if __name__ == "__main__":
    app.run(debug=True)