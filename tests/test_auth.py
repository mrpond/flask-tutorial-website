import pytest
from flask import g, session
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db


def test_register(client, app):
    assert client.get("/auth/register").status_code == 200
    response = client.post(
        "/auth/register",
        data={"username": "a", "password": "a"},
        follow_redirects=True,
    )
    message = b"User registration completed, you can now login with a"
    # assert response.headers["Location"] == "/auth/login" and response.status_code == 302
    assert message in response.data
    with app.app_context():
        account = (
            get_db()
            .execute(
                text("SELECT * FROM user WHERE username = :username"),
                {"username": "a"},
            )
            .fetchone()
        )
        assert account is not None


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Username and password is required."),
        ("a", "", b"Username and password is required."),
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
    ("current_password", "new_password", "confirm_new_password", "message"),
    (
        ("", "newpassword", "newpassword", b"Current password is required."),
        ("test", "", "newpassword", b"New password is required."),
        ("test", "newpassword", "", b"Confirm new password is required."),
        ("test", "newpassword", "mismatchpassword", b"New passwords do not match."),
        ("xxx", "newpassword", "newpassword", b"Current password is incorrect."),
        ("test", "test", "test", b"New passwords is the same as current password."),
        (
            "test",
            "newpassword",
            "newpassword",
            b"Password change completed, you can now login with new password.",
        ),
    ),
)
def test_change_password(
    client, auth, app, current_password, new_password, confirm_new_password, message
):
    assert client.get("/auth/login").status_code == 200
    response = auth.login()
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    # Go to the change password page
    response = client.get("/auth/change_password")
    assert response.status_code == 200

    # Test password change with invalid inputs
    response = client.post(
        "/auth/change_password",
        data={
            "current_password": current_password,
            "new_password": new_password,
            "confirm_new_password": confirm_new_password,
        },
        follow_redirects=True,
    )
    assert message in response.data


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("a", "test", b"Incorrect username or password."),
        ("test", "a", b"Incorrect username or password."),
    ),
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password, follow_redirects=True)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert "id" not in session
