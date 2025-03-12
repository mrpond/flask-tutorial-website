import uuid
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

import httpx
from flask import Flask, current_app


class Turnstile:
    """Flask extension for Cloudflare Turnstile CAPTCHA integration."""

    # https://developers.cloudflare.com/turnstile/

    # https://developers.cloudflare.com/turnstile/troubleshooting/testing/
    DUMMY_TOKEN = "XXXX.DUMMY.TOKEN.XXXX"
    VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    DUMMY_SITE_KEYS = [
        "1x00000000000000000000AA",  # Always passes	visible
        "2x00000000000000000000AB",  # Always blocks	visible
        "1x00000000000000000000BB",  # Always passes	invisible
        "2x00000000000000000000BB",  # Always blocks	invisible
        "3x00000000000000000000FF",  # Forces an interactive challenge	visible
    ]
    DUMMY_SECRET_KEYS = [
        "1x0000000000000000000000000000000AA",  # Always passes
        "2x0000000000000000000000000000000AA",  # Always fails
        "3x0000000000000000000000000000000AA",  # Yields a "token already spent" error
    ]
    __widgets: Dict[str, str] = {}  # Private: widget name -> site_key
    __secret_keys: Dict[str, str] = {}  # Private: widget name -> secret_key

    def __init__(self, app=None) -> None:
        """
        Initialize the Flask_CF_Turnstile extension.

        Args:
            app: Optional Flask application instance for immediate initialization. Defaults to None.
        """
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Initialize the extension with a Flask application instance.

        Args:
            app: The Flask application instance to configure.

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
            }
        """
        config = app.config.get("CF_TURNSTILE_CONFIG")
        if config is None:
            raise SystemError("CF_TURNSTILE_CONFIG cannot be none")
        else:
            for widget_name, data in config.items():
                if not isinstance(data, (dict, Mapping)):
                    raise ValueError(
                        f"config for '{widget_name}' must be a mapping, got {type(data)}"
                    )

                if all(key in data for key in ("site_key", "secret_key")):
                    # Store site_key in private __widgets
                    self.__widgets[widget_name] = str(data["site_key"])
                    # Store secret_key in private __secret_keys
                    self.__secret_keys[widget_name] = str(data["secret_key"])

                    if not app.debug:
                        if self.__check_dummy_site_key(str(data["site_key"])):
                            raise SystemError(
                                f"Turnstile dummy site key detected for '{widget_name}': {data}. "
                            )
                        if self.__check_dummy_secret_key(str(data["secret_key"])):
                            raise SystemError(
                                f"Turnstile dummy secret key detected for '{widget_name}': {data}. "
                            )
                else:
                    raise ValueError(
                        f"Invalid widget config for '{widget_name}': {data}. "
                        "Must contain 'site_key' and 'secret_key'"
                    )

        app.turnstile = self  # Store instance in app for easy access

        @app.context_processor
        def inject_config() -> dict[str, str]:
            """Inject Turnstile site key into templates."""
            return {"cf_turnstile_site_key": self.__widgets}

    def __check_dummy_site_key(self, site_key: str) -> bool:
        return site_key in self.DUMMY_SITE_KEYS

    def __check_dummy_secret_key(self, secret_key: str) -> bool:
        return secret_key in self.DUMMY_SECRET_KEYS

    def __get_secret_key(self, widget_name: str) -> str:
        """
        Private method to retrieve the secret key for a given widget.

        Args:
            widget_name: The name of the widget to get the secret key for.

        Returns:
            str: The secret key for the widget.
        """
        if widget_name is None:
            widget_name = "default"

        if widget_name in self.__secret_keys:
            return self.__secret_keys[widget_name]
        raise ValueError(f"No secret key found for widget '{widget_name}'")

    def get_site_key(self, widget_name: str) -> str:
        """
        Private method to retrieve the site key for a given widget.

        Args:
            widget_name: The name of the widget to get the site key for.

        Returns:
            str: The site key for the widget.
        """
        if widget_name is None:
            widget_name = "default"

        if widget_name in self.__widgets:
            return self.__widgets[widget_name]

        raise ValueError(f"No site key found for widget '{widget_name}'")

    def __post_siteverify_api(
        self, secret_key: str, token: str, client_ip: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a POST request to Cloudflare Turnstile verification endpoint.

        Args:
            secret_key: The secret key for the widget.
            token: The response token from the client-side Turnstile widget.
            client_ip: Optional client IP address to include in verification.

        Returns:
            Dict[str, Any] | None: The JSON response from Cloudflare, or None if the request fails.
        """
        idempotency_key = str(uuid.uuid4())  # Generate a random UUID
        data = {
            "secret": secret_key,
            "response": token,
            "idempotency_key": idempotency_key,
        }

        if client_ip is not None:
            data["remoteip"] = client_ip

        with httpx.Client() as client:
            try:
                response = client.post(self.VERIFY_URL, data=data).json()

                if not response.get("success", False):
                    response = client.post(self.VERIFY_URL, data=data).json()

                return response
            except Exception as e:
                raise e

    def verify(
        self,
        widget_name: str = None,
        token: str = None,
        client_ip: str = None,
        verify_callback: Optional[
            Callable[[Dict[str, Any]], Tuple[bool, list[str]]]
        ] = None,
        **callback_kwargs,
    ) -> Tuple[bool, list[str]]:
        """
        Verify a Cloudflare Turnstile response token with an optional additional verification callback.

        Args:
            widget_name: The name of the widget to verify against (defaults to "default").
            token: The response token from the client-side Turnstile widget.
            client_ip: Optional client IP address to include in verification.
            verify_callback: Optional callback function to perform additional verification.
                            Takes the response dict and returns (success, errors).
            **callback_kwargs: Variable keyword arguments to pass to the callback.

        Returns:
            Tuple[bool, list[str]]: (success status, list of error messages or success message)
        """
        # https://developers.cloudflare.com/turnstile/get-started/server-side-validation/

        result = False
        if not token:
            return result, ["missing-input-response"]

        if token == self.DUMMY_TOKEN and not current_app.debug:
            return result, ["turnstile DUMMY_TOKEN detected in Production"]

        try:
            cf_secret = self.__get_secret_key(widget_name)
            response = self.__post_siteverify_api(cf_secret, token, client_ip)
        except ValueError as e:
            return result, [str(e)]

        result = response.get("success", False)
        if result is False:
            return result, response.get("error-codes", ["turnstile unknown API error"])

        message = ["turnstile API verification OK"]

        if verify_callback is not None:
            result, message = verify_callback(response=response, **callback_kwargs)

        return result, message
