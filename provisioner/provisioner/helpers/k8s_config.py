import os
from kubernetes import config
from kubernetes.config.config_exception import ConfigException
from helpers.config import CURAPACS_CONFIG

#https://github.com/kubernetes-client/python/blob/master/examples/in_cluster_config.py

def load_kubernetes_config():
    """
    tries to load from k8s_auth_file, if file not found, try loading with service account credentials
    """
    try:
        if os.path.isfile(CURAPACS_CONFIG["k8s_auth_file"]):
            config.load_kube_config(config_file=CURAPACS_CONFIG["k8s_auth_file"])
            return
    except FileNotFoundError:
        print("Failed to import kubeconfig at " + CURAPACS_CONFIG["k8s_auth_file"])
    try:
        config.load_incluster_config()
    except ConfigException:
        print("Also failed to load incluster config, aborting.")
        raise
