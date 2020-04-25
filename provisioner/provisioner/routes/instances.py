from flask import jsonify
from provisioner import app


@app.route("/instances", methods=["GET","POST"])
@app.route("/instances/<instance_id>", methods=["GET"])
def instances(instance_id=None):
    return jsonify([])
