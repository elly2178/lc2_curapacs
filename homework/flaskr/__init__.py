import os
from flask import Flask

def create_app(test_config=None):
    #create and config the app

    # created the FLask instance
    # __name__ : name of the current python moduele
    # instance_relative_config: tellst he app that configuration files are RELATIVE to INSTANCE FOLDER
    # instance folder is located outside the flaskr folder
    app = Flask(__name__, instance_relative_config=True)
    #app.config.from_mapping: sets some default configuration that the app will use
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE = os.path.join(app.instance_path,
        'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent =True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says FUCK ME LIFE
    @app.route('/hello')
    def hello():
        return 'Oh GOd help me'
    return app