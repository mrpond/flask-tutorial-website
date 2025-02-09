import os
import tempfile

import pytest
from sqlalchemy import text

from flaskr import create_app
from flaskr.db import executescript, get_db, init_db

with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(
        {
            "TESTING": True,
            "SQLITE_PATH": db_path,
            # "SQLALCHEMY_DATABASE_URI": "mariadb+mariadbconnector://root:123456@localhost:3306/flaskr",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        }
    )

    with app.app_context():
        init_db()
        executescript(_data_sql)
        db = get_db()
        # this can't put into data.sql, since sqlite will escape the \ into \\,
        # this make the test fail, since we want newline not the escape \
        db.execute(
            text(
                "INSERT INTO post (title, body, author_id, created) VALUES (:title, :body, :author_id, :created)"
            ),
            {
                "title": "test title",
                "body": "test\nbody",
                "author_id": 1,
                "created": "2018-01-01 00:00:00",
            },
        )
        db.commit()
    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username="test", password="test", follow_redirects=False):
        return self._client.post(
            "/auth/login",
            data={"username": username, "password": password},
            follow_redirects=follow_redirects,
        )

    def logout(self, follow_redirects=False):
        return self._client.get("/auth/logout", follow_redirects=follow_redirects)


@pytest.fixture
def auth(client):
    return AuthActions(client)
