from flask import jsonify
from provisioner import app, v1

@app.route("/instances", methods=["GET", "POST"])
@app.route("/instances/<instance_id>", methods=["GET"])
def instances(instance_id=None):
    ns_list = v1.list_namespace(watch=False)
    return jsonify(v1.list_pod_for_all_namespaces(watch=False))
