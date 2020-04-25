from flask import Flask
from provisioner import app
from provisioner import helpers
import sys
print(sys.path)
import provisioner.routes 

def main():
    app.run(host="0.0.0.0", debug=True)
