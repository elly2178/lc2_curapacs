from flask import Flask
app = Flask(__name__)

from provisioner import run

if __name__ == '__main__':
    sys.exit(run.main())





