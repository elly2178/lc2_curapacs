from os import getenv

CURAPACS_CONFIG = {
        "namespace" : getenv("CURAPACS_NAMESPACE", "curapacs"),
        "manifests_dir" : getenv("CURAPACS_MANIFESTS_DIR", "/opt/provisioner/kubernetes"),
        "k8s_auth_file" : getenv("CURAPACS_K8S_AUTH_FILE", "/opt/provisioner/auth.yml"),
        "dicom_port_min" : getenv("CURAPACS_DICOM_PORT_MIN", "6666"),
        "dicom_port_max" : getenv("CURAPACS_DICOM_PORT_MAX", "9999"),
        "provisioner_port" : getenv("CURAPACS_PROVISIONER_PORT", "8080"),
        "provisioner_host" : getenv("CURAPACS_PROVISIONER_HOST", "0.0.0.0"),
        "kustomize_overlay_environment": getenv("CURAPACS_KUSTOMIZE_OVERLAY_ENVIRONMENT", "staging")
        }

CURAPACS_K8S_COMPONENTS = {
        "orthanc": {},
        "orthanc-postgres": {},
        "meddream-viewer": {},
        "meddream-tokenservice": {}
}