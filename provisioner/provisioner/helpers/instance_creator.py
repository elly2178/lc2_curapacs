import subprocess
from flask_restful import abort, reqparse
from helpers.config import CURAPACS_CONFIG, CURAPACS_K8S_COMPONENTS


def manipulate_components(curapacs_customer, mode="apply", components=[], curapacs_domain=CURAPACS_CONFIG['curapacs_domain']):
    if not components:
        components = CURAPACS_K8S_COMPONENTS
    else:
        for component in components:
            if component not in CURAPACS_K8S_COMPONENTS:
                abort(400, message=f"Unknown component {component}.")
    if mode not in ("apply", "delete"):
        abort(400, message=f"Bad mode {mode} detected")
    for component in components:
        try:
            kustomize_output = subprocess.Popen(f"kustomize build {CURAPACS_CONFIG['manifests_dir']}/{component}/overlays/{CURAPACS_CONFIG['kustomize_overlay_environment']}/ | python3 {CURAPACS_CONFIG['manifests_dir']}/templating.py --CURAPACS_DOMAIN {curapacs_domain} --CURAPACS_CUSTOMER {curapacs_customer} | kubectl {mode} -f -",
                                            stdin=subprocess.PIPE,
                                            shell=True)
            """
            templating_output = subprocess.Popen(f"{CURAPACS_CONFIG['manifests_dir']}/templating.py --CURAPACS_DOMAIN {CURAPACS_DOMAIN} --CURAPACS_CUSTOMER {CURAPACS_CUSTOMER}".split(),
                                            stdin=kustomize_output.stdout,
                                            stdout=subprocess.PIPE)
            kubectl_output = subprocess.Popen(f"kubectl {mode} -f -".split(),
                                            stdin=templating_output.stdout,
                                            stdout=subprocess.PIPE)
            """
        except subprocess.CalledProcessError as error:
            abort(400, message=f"{error.cmd} failed, status {error.returncode}, output: {error.stdout}, stderr: {error.stderr}")

