import os
from flask import Flask
import secrets


def create_app(custom_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=get_secret_key(os.path.join(app.instance_path, "secret_key")),
        SQLITE_PATH=os.path.join(app.instance_path, "flaskr.sqlite"),
        #SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, "flaskr.sqlite")}",
        SQLALCHEMY_DATABASE_URI="mariadb+mariadbconnector://root:123456@localhost:3306/flaskr",
    )

    if custom_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(custom_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route("/hello")
    def hello():
        return "Hello, World!"

    from . import db

    db.init_app(app)

    from . import auth

    app.register_blueprint(auth.bp)

    from . import blog

    app.register_blueprint(blog.bp)
    app.add_url_rule("/", endpoint="index")

    return app


def get_secret_key(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            key = secrets.token_hex(16)
            f.write(key)
    else:
        with open(path, "r") as f:
            key = f.read().strip()
    return key
