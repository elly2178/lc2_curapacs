from flask import Flask
from provisioner import app
from provisioner import helpers
import provisioner.routes 
import provisioner.helpers
from provisioner.config import curapacs_config

def main():
    app.run(host=curapacs_config["provisioner_host"],
            port=curapacs_config["provisioner_port"],
            debug=True)
