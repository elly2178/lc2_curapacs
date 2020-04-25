#reads environment and sets defaults if necessary
from os import environ

curapacs_config = { 
        "basename" : getenv("CURAPACS_BASENAME","curapacs"),
        "manifests_dir" : getenv("CURAPACS_MANIFESTS_DIR","/opt/provisioner/manifests"),
        "dicom_port_min" : getenv("CURAPACS_DICOM_PORT_MIN","6666"),
        "dicom_port_max" : getenv("CURAPACS_DICOM_PORT_MAX","9999"),
        "provisioner_port" : getenv("CURAPACS_PROVISIONER_PORT","8080")
        }

#TODO sanity check
