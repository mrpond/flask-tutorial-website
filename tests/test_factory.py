import pytest

from flaskr import create_app


def test_config():
    with pytest.raises(SystemError):
        assert not create_app().testing


def test_config_test():
    assert create_app({"TESTING": True}).testing


def test_missing_config(app):
    with pytest.raises(ValueError):
        create_app(
            {
                "CF_TURNSTILE_CONFIG": {
                    "login": {
                        "site_key": "3x00000000000000000000FF",
                    },
                }
            }
        )


def test_mismatch_config(app):
    with pytest.raises(ValueError):
        create_app({"CF_TURNSTILE_CONFIG": {"login": 000}})


def test_malform_config(app):
    with pytest.raises(ValueError):
        create_app(
            {
                "CF_TURNSTILE_CONFIG": {
                    "login": {
                        "malform1": "3x00000000000000000000FF",
                        "malform2": "3x00000000000000000000FF",
                    },
                }
            }
        )


def test_config_no_data():
    with pytest.raises(SystemError):
        create_app({"CF_TURNSTILE_CONFIG": None})


def test_hello(client):
    response = client.get("/hello")
    assert response.data == b"Hello, World!"
