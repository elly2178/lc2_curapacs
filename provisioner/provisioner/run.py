import provisioner.helpers
import provisioner.routes
from provisioner import app
from provisioner.config import CURAPACS_CONFIG


def main():
    app.run(host=CURAPACS_CONFIG["provisioner_host"],
            port=CURAPACS_CONFIG["provisioner_port"],
            debug=True)
