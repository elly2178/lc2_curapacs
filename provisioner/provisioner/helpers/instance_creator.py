import subprocess
from flask_restful import abort
from helpers.config import CURAPACS_CONFIG, CURAPACS_K8S_COMPONENTS


CURAPACS_DOMAIN = "curapacs.ch"
CURAPACS_CUSTOMER = "c0100"

#kustomize build  kubernetes/provisioner/overlays/staging/ | 
#python3 kubernetes/templating.py --CURAPACS_DOMAIN curapacs.ch --CURAPACS_CUSTOMER c0100 | 
#kubectl apply -f -
CURAPACS_K8S_COMPONENTS = ["meddream-viewer"]

def manipulate_components(mode="apply"):
    if mode not in ("apply","delete"):
        abort(400, message=f"Bade mode {mode} detected")
    for component in CURAPACS_K8S_COMPONENTS:
        try:
            kustomize_output = subprocess.run(f"kustomize build {CURAPACS_CONFIG['manifests_dir']}/{component}/overlays/{CURAPACS_CONFIG['kustomize_overlay_environment']}/".split(),
                                            stdout=subprocess.PIPE,
                                            check=True)
            templating_output = subprocess.run(f"{CURAPACS_CONFIG['manifests_dir']}/templating.py --CURAPACS_DOMAIN {CURAPACS_DOMAIN} --CURAPACS_CUSTOMER {CURAPACS_CUSTOMER}".split(),
                                            stdin=kustomize_output.stdout,
                                            stdout=subprocess.PIPE,
                                            check=True)
            kubectl_output = subprocess.run(f"kubectl {mode} -f -".split(),
                                            stdin=templating_output.stdout,
                                            stdout=subprocess.PIPE,
                                            check=True)
        except subprocess.CalledProcessError as error:
            abort(400, message=f"{error.cmd} failed, status {error.returncode}, output: {error.stdout}, stderr: {error.stderr}")

