import os
import secrets

from flask import Flask


def create_app(custom_config=None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # ensure the instance folder exists>
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config.from_mapping(
        SECRET_KEY=get_secret_key(os.path.join(app.instance_path, "secret_key")),
        SQLITE_PATH=os.path.join(app.instance_path, "flaskr.sqlite"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'flaskr.sqlite')}",
        CF_TURNSTILE_SITE_KEY= "3x00000000000000000000FF", #"1x00000000000000000000AA",
        CF_TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA",
        # SQLALCHEMY_DATABASE_URI="mariadb+mariadbconnector://root:123456@localhost:3306/flaskr",
    )

    if custom_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(custom_config)

    # a simple page that says hello
    @app.route("/hello")
    def hello():
        return "Hello, World!"

    from . import db

    db.init_app(app)

    from . import turnstile

    turnstile.init_app(app)

    from . import auth

    app.register_blueprint(auth.bp)

    from . import blog

    app.register_blueprint(blog.bp)

    from . import manage

    app.register_blueprint(manage.bp)

    app.add_url_rule("/", endpoint="index")

    return app


def get_secret_key(path: str) -> str:
    if not os.path.exists(path):
        with open(path, "w") as f:
            key = secrets.token_hex(16)
            f.write(key)
    else:
        with open(path, "r") as f:
            key = f.read().strip()
    return key
