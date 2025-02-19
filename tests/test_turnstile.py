import pytest

from flaskr.turnstile import cf_turnstile_verify

TURNSTILE_DUMMY_TOKEN = "XXXX.DUMMY.TOKEN.XXXX"


def test_captcha_fail(client, app):
    with app.app_context():
        app.config.update(
            {
                "TESTING": False,
                "CF_TURNSTILE_SITE_KEY": "1x00000000000000000000AA",
                "CF_TURNSTILE_SECRET_KEY": "1x0000000000000000000000000000000AA",
            }
        )
        response = client.post(
            "/auth/register",
            data={"username": "a", "password": "a"},
            follow_redirects=True,
        )
        message = b"Captcha verification failed"
        assert message in response.data


@pytest.mark.parametrize(
    ("cf_secret_key", "cf_site_key", "expected_result", "expected_message"),
    (
        ("", "1x00000000000000000000AA", False, ["turnstile secret key not set"]),
        ("1x0000000000000000000000000000000AA", "1x00000000000000000000AA", True, []),
        (
            "2x0000000000000000000000000000000AA",
            "1x00000000000000000000BB",
            False,
            ["invalid-input-response"],
        ),
        (
            "3x0000000000000000000000000000000AA",
            "1x00000000000000000000BB",
            False,
            ["timeout-or-duplicate"],
        ),
    ),
)
def test_verify(
    client, app, cf_secret_key, cf_site_key, expected_result, expected_message
):
    with app.app_context():
        app.config.update(
            {
                "CF_TURNSTILE_SECRET_KEY": cf_secret_key,
                "CF_TURNSTILE_SITE_KEY": cf_site_key,
            }
        )

        cf_response, cf_message = cf_turnstile_verify(TURNSTILE_DUMMY_TOKEN)
        # Assertions
        assert expected_result is cf_response
        assert expected_message == cf_message


def test_verify_failed(client, app):
    with app.app_context():
        cf_response, cf_message = cf_turnstile_verify("")
        # Assertions
        assert cf_response is False
        assert "missing-input-response" in cf_message
