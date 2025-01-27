import pytest
from flask import g, session
from flaskr.db import get_db


def test_register(client, app):
    assert client.get("/auth/register").status_code == 200
    response = client.post(
        "/auth/register",
        data={"username": "a", "password": "a"},
        follow_redirects=True,
    )
    message = b"User registeration completed, you can now login with a"
    # assert response.headers["Location"] == "/auth/login" and response.status_code == 302
    assert message in response.data
    with app.app_context():
        account = get_db().query_single(
            "SELECT * FROM user WHERE username = 'a'",
        )
        assert account is not None


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Username is required."),
        ("a", "", b"Password is required."),
        ("test", "test", b"User test is already registered."),
    ),
)
def test_register_validate_input(client, username, password, message):
    response = client.post(
        "/auth/register",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert message in response.data


def test_login(client, auth):
    assert client.get("/auth/login").status_code == 200
    response = auth.login()
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    with client:
        client.get("/")
        assert session["id"] is not None
        assert g.user is not None
        assert session["id"] > 0
        assert g.user["username"] == "test"


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("a", "test", b"Incorrect username or password."),
        ("test", "a", b"Incorrect username or password."),
    ),
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert "id" not in session
