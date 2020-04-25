from flask import Flask
app = Flask(__name__)

from provisioner import run
from sys import exit

if __name__ == '__main__':
    exit(run.main())





