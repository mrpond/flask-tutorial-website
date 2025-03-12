import pytest


def test_get_site_key(app):
    with app.app_context():
        turnstile = app.extensions["turnstile"]
        # Assertions
        config = app.config.get("CF_TURNSTILE_CONFIG")
        result = turnstile.get_site_key()
        site_keys = [data["site_key"] for _, data in config.items()]

        assert result in site_keys


def test_get_site_key_fail(app):
    with app.app_context():
        turnstile = app.extensions["turnstile"]
        with pytest.raises(ValueError):
            turnstile.get_site_key("not existing")


def test_captcha_fail(client, app):
    with app.app_context():
        app.config.update(
            {
                "TESTING": False,
            }
        )
        response = client.post(
            "/auth/register",
            data={"username": "a", "password": "a", "confirm_password": "a"},
            follow_redirects=True,
        )
        message = b"Captcha verification failed"
        assert message in response.data


def test_dummy_token_production(app):
    with app.app_context():
        app.config.update(
            {
                "TESTING": False,
            }
        )
        turnstile = app.extensions["turnstile"]
        result, message = turnstile.verify("", "XXXX.DUMMY.TOKEN.XXXX")
        assert result is False
        assert message == ["turnstile DUMMY_TOKEN detected in Production"]


@pytest.mark.parametrize(
    ("widget_name", "token", "expected_result", "expected_message"),
    (
        ("default", "XXXX.DUMMY.TOKEN.XXXX", True, ["turnstile API verification OK"]),
        ("default", "", False, ["missing-input-response"]),
    ),
)
def test_verify(app, widget_name, token, expected_result, expected_message):
    with app.app_context():
        turnstile = app.extensions["turnstile"]
        result, message = turnstile.verify(
            widget_name=widget_name,
            token=token,
        )
        # Assertions
        assert expected_result is result
        assert expected_message == message


def test_verify_callback(app):
    def dummy_callback(response):
        return True, ["turnstile API verification OK"]

    with app.app_context():
        turnstile = app.extensions["turnstile"]
        result, message = turnstile.verify(
            widget_name="default",
            token="XXXX.DUMMY.TOKEN.XXXX",
            client_ip="127.0.0.1",
            verify_callback=dummy_callback,
        )
        # Assertions
        assert result is True
        assert message == ["turnstile API verification OK"]
