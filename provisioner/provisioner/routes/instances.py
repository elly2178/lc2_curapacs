from flask import jsonify
from provisioner import app, k8s_corev1
from provisioner.config import CURAPACS_CONFIG

@app.route("/instances", methods=["GET", "POST"])
@app.route("/instances/<instance_id>", methods=["GET"])
def instances(instance_id=None):
    instance_dict = {}
    pod_list = k8s_corev1.list_namespaced_pod(watch=False, namespace=CURAPACS_CONFIG["namespace"])
    for pod_definition in pod_list.items:
        labels = pod_definition.metadata.labels
        containers = pod_definition.spec.containers
        if labels["curamed.ch/customer"] not in instance_dict:
            instance_dict[labels["curamed.ch/customer"]] = {}
        instance_dict[labels["curamed.ch/customer"]][labels["app.kubernetes.io/name"]] = containers[0].image

    return jsonify(instance_dict)
