import functools
from typing import Dict, Mapping, Tuple

import httpx
from flask import Flask, current_app, flash, redirect, request
import ipaddress

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class Flask_CF_Turnstile:
    """Flask extension for Cloudflare Turnstile CAPTCHA integration."""

    def __init__(self, app=None) -> None:
        """
        Initialize the Flask_CF_Turnstile extension.

        Args:
            app: Optional Flask application instance for immediate initialization. Defaults to None.
        """
        self.widget_list: Dict[str, Dict[str, str]] = {}  # Store widget configurations
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Initialize the extension with a Flask application instance.

        Args:
            app: The Flask application instance to configure.
            config: Optional mapping of widget names to their configurations.
                Example:
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
        """
        config = app.config.get("CF_TURNSTILE_CONFIG")
        if config is None:
            raise SystemError("CF_TURNSTILE_CONFIG cannot be none")
        else:
            for widget_name, data in config.items():
                # Ensure widget_data is a dict-like object with required keys
                if not isinstance(data, (dict, Mapping)):
                    raise ValueError(
                        f"config for '{widget_name}' must be a mapping, got {type(data)}"
                    )

                if all(key in data for key in ("site_key", "secret_key")):
                    self.widget_list[widget_name] = {
                        "site_key": str(data["site_key"]),
                        "secret_key": str(data["secret_key"]),
                    }
                else:
                    raise ValueError(
                        f"Invalid widget config for '{widget_name}': {data}. "
                        "Must contain 'site_key' and 'secret_key'"
                    )

        app.turnstile = self  # Store instance in app for easy access

        @app.context_processor
        def inject_config() -> dict[str, str]:
            """Inject Turnstile site key into templates."""
            return {
                "cf_turnstile_site_key": {
                    name: config["site_key"]
                    for name, config in self.widget_list.items()
                }
            }

    def cf_turnstile_verify(
        self, widget_name: str, cf_response_token: str, client_ip: str = None
    ) -> Tuple[bool, list[str]]:
        """
        Verify a Cloudflare Turnstile response token.

        Args:
            widget_name: The name of the widget to verify against
            cf_response_token: The response token from the client-side Turnstile widget.

        Returns:
            Tuple[bool, list[str]]: (success status, list of error messages or codes)
        """
        cf_secret = None

        if not cf_response_token:
            return False, ["missing-input-response"]

        if widget_name is None:
            widget_name = "default"

        if widget_name in self.widget_list:
            cf_secret = self.widget_list[widget_name]["secret_key"]
        else:
            return False, ["turnstile secret key not set"]

        data = {
            "secret": cf_secret,
            "response": cf_response_token,
        }

        if client_ip is not None:
            data["remoteip"] = client_ip

        with httpx.Client() as client:
            try:
                response = client.post(TURNSTILE_VERIFY_URL, data=data).json()
                return response.get("success", False), response.get(
                    "error-codes", ["turnstile API error"]
                )
            except Exception as e:
                return False, [str(e)]


# Check if an IP is in a list of CIDR ranges
def is_ip_in_cidr(ip, cidr_list):
    try:
        ip_obj = ipaddress.ip_address(ip)
        for cidr in cidr_list:
            network = ipaddress.ip_network(cidr, strict=False)
            if ip_obj in network:
                return True
    except Exception:
        pass
    return False


def cf_get_client_ip() -> str:
    client_ip = request.remote_addr
    is_cloudflare_ip = is_ip_in_cidr(
        client_ip, current_app.config.get("CF_IPV4")
    ) or is_ip_in_cidr(client_ip, current_app.config.get("CF_IPV6"))
    if is_cloudflare_ip is True:
        return request.headers.get("CF-Connecting-IP", client_ip)
    return client_ip


def cf_turnstile_required(widget_name: str = None):
    """
    Decorator to require Turnstile CAPTCHA verification on POST requests.

    Args:
        view: The view function to decorate.

    Returns:
        Callable[..., Any]: Decorated view function.
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            testing = current_app.testing

            if request.method == "POST" and not testing:
                cf_response_token = request.form.get("cf-turnstile-response")
                
                result, message = current_app.turnstile.cf_turnstile_verify(
                    widget_name, cf_response_token, cf_get_client_ip()
                )

                if not result:
                    error_msg = (
                        ", ".join(message) if isinstance(message, list) else message
                    )
                    flash(f"Captcha verification failed: {error_msg}")
                    return redirect(request.url)

            return view(**kwargs)

        return wrapped_view

    return decorator
