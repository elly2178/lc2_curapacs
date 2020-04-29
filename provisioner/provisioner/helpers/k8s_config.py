from kubernetes import client, config
from provisioner.config import CURAPACS_CONFIG

def import_kubernetes_config():

    try:
        config.load_kube_config(config_file=CURAPACS_CONFIG["k8s_auth_file"])
    except:
        print("failed to import kubeconfig at " + CURAPACS_CONFIG["k8s_auth_file"])
    return (client.CoreV1Api())
