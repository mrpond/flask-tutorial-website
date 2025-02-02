import pytest
from flask import g, session
from flaskr.db import get_db
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash


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


# Test for successful password change
def test_change_password_success(client, auth, app):
    assert client.get("/auth/login").status_code == 200
    response = auth.login()
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    # Go to the change password page
    response = client.get("/auth/change_password")
    assert response.status_code == 200

    # Test correct password change
    response = client.post(
        "/auth/change_password",
        data={
            "current_password": "test",
            "new_password": "newpassword",
            "confirm_new_password": "newpassword",
        },
        follow_redirects=True,
    )
    assert (
        response.status_code == 200
    )  # Assuming this is where the flash message is displayed after redirect
    assert (
        b"Password change completed, you can now login with new password."
        in response.data
    )

    # Check if user is logged out after password change
    with client:
        client.get("/")
        assert "id" not in session
        assert g.user is None

    # Test login with new password
    response = auth.login(password="newpassword")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    # Verify password has been changed in the database
    with app.app_context():
        db = get_db()
        result = db.execute(
            text("SELECT password FROM user WHERE username = :username"),
            {"username": "test"},
        ).scalar_one_or_none()
        assert result is not None
        assert check_password_hash(result, "newpassword")

    # Reset password for other tests (assuming 'test' as the original password)
    with app.app_context():
        db = get_db()
        db.execute(
            text("UPDATE user SET password = :password WHERE username = :username"),
            {"username": "test", "password": generate_password_hash("test")},
        )
        db.commit()


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
