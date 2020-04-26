import sys
from flask import Flask
from os import getcwd

sys.path.append(getcwd())
app = Flask(__name__)

from provisioner.helpers import k8s_config
k8s_corev1, k8s_appsv1 = k8s_config.import_kubernetes_config()

from provisioner import run

if __name__ == '__main__':
    sys.exit(run.main())
