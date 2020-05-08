from kubernetes import client, config
from provisioner.config import CURAPACS_CONFIG

def import_kubernetes_config():
    try:
        config.load_kube_config(config_file=CURAPACS_CONFIG["k8s_auth_file"])
    except FileNotFoundError:
        print("failed to import kubeconfig at " + CURAPACS_CONFIG["k8s_auth_file"])
        raise
    return client.CoreV1Api(), client.AppsV1Api()
