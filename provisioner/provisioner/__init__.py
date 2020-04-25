from flask import Flask
app = Flask(__name__)

from sys import exit, path
from os import getcwd

path.append(getcwd())
from provisioner import run

if __name__ == '__main__':
    exit(run.main())





