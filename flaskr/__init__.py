import os
import secrets

from flask import Flask
from .flask_cf_turnstile import Flask_CF_Turnstile
import httpx

CLOUDFLARE_IP_LIST_URL = "https://api.cloudflare.com/client/v4/ips"


def create_app(custom_config=None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # ensure the instance folder exists>
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    CF_IPV4_CIDRS, CF_IPV6_CIDRS = get_cloudflare_cidrs()

    app.config.from_mapping(
        SECRET_KEY=get_secret_key(os.path.join(app.instance_path, "secret_key")),
        SQLITE_PATH=os.path.join(app.instance_path, "flaskr.sqlite"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'flaskr.sqlite')}",
        # SQLALCHEMY_DATABASE_URI="mariadb+mariadbconnector://root:123456@localhost:3306/flaskr",
        CF_TURNSTILE_CONFIG={
            "login": {
                "site_key": "3x00000000000000000000FF",
                "secret_key": "1x0000000000000000000000000000000AA",
            },
            "default": {
                "site_key": "1x00000000000000000000AA",
                "secret_key": "1x0000000000000000000000000000000AA",
            },
        },
        CF_IPV4_LIST=CF_IPV4_CIDRS,
        CF_IPV6_LIST=CF_IPV6_CIDRS,
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

    # from . import turnstile

    turnstile = Flask_CF_Turnstile()
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


def get_cloudflare_cidrs():
    try:
        with httpx.Client() as client:
            response = client.get(CLOUDFLARE_IP_LIST_URL)
            data = response.json()
            if data["success"]:
                return data["result"]["ipv4_cidrs"], data["result"]["ipv6_cidrs"]
            else:
                pass
    except Exception:
        raise SystemError("fail to get cloudflare IP list")
        pass
    return [], []
