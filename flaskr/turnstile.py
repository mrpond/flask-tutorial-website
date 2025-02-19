import functools
from typing import Tuple

import httpx
from flask import (
    current_app,
    flash,
    redirect,
    request,
)


def cf_turnstile_verify(cf_response_token: str) -> Tuple[bool, str]:
    cf_secret = current_app.config.get("CF_TURNSTILE_SECRET_KEY")
    if not cf_secret:
        return False, ["turnstile secret key not set"]

    if not cf_response_token:
        return False, ["missing-input-response"]

    # Prepare data for the POST request
    data = {
        "secret": cf_secret,
        "response": cf_response_token,
    }
    # First validation request
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    client = httpx.Client()
    try:
        response = client.post(url, data=data).json()
        return response.get("success"), response.get("error-codes")

    except Exception as e:
        return False, f"{e}"


def cf_turnstile_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        testing = current_app.config.get("TESTING", False)

        if request.method == "POST" and testing is False:
            # Retrieve form data
            cf_response_token = request.form.get("cf-turnstile-response")

            result, message = cf_turnstile_verify(cf_response_token)

            if result is False:
                flash(f"Captcha verification failed {message}")
                return redirect(request.url)

        return view(**kwargs)

    return wrapped_view


def init_app(app):
    @app.context_processor
    def inject_config():
        return dict(cf_site_key=app.config.get("CF_TURNSTILE_SITE_KEY"))
