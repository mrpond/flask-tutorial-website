import os
from flask import Flask

def create_app(custom_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DB_TYPE = 'sqlite', # choice 'mariadb' or 'sqlite'
        SQLITE_PATH = os.path.join(app.instance_path, 'flaskr.sqlite'),
        DATABASE = {
            "user": "root",
            "password": "123456",
            "host": "localhost",
            "port": 3306,
            "database": "flaskr",
        },
    )

    if custom_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(custom_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')
    
    return app
