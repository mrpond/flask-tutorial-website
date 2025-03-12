import functools
import ipaddress
from typing import Any, Dict, Optional, Tuple

from flask import current_app, flash, redirect, request


# Check if an IP is in a list of CIDR ranges
def is_ip_in_cidr(ip: str, cidr_list: Optional[list[str]]) -> bool:
    """Check if an IP is in a list of CIDR ranges."""
    if not cidr_list:
        return False
    try:
        ip_obj = ipaddress.ip_address(ip)
        for cidr in cidr_list:
            network = ipaddress.ip_network(cidr, strict=False)
            if ip_obj in network:
                return True
    except ValueError:
        return False
    return False


def cf_get_client_ip() -> str:
    """Get the client's IP address, accounting for Cloudflare headers."""
    client_ip = request.remote_addr
    is_cloudflare_ip = is_ip_in_cidr(
        client_ip, current_app.config.get("CF_IPV4")
    ) or is_ip_in_cidr(client_ip, current_app.config.get("CF_IPV6"))
    if is_cloudflare_ip:
        return request.headers.get("CF-Connecting-IP", client_ip)
    return client_ip


def is_local() -> bool:
    """Check if the request comes from a local IP address."""
    LOCAL_IP = ["127.0.0.1", "::1"]
    return request.remote_addr in LOCAL_IP


def cf_turnstile_additional_verify(
    response: Dict[str, Any],
    action: Optional[str] = None,
    cdata: Optional[str] = None,
) -> Tuple[bool, list[str]]:
    """
    Verify the Cloudflare Turnstile response JSON with additional checks.

    Args:
        response: The JSON response from the Turnstile verification endpoint.
        action: Optional expected action string to verify against the response.
        cdata: Optional expected client data to verify against the response.

    Returns:
        Tuple[bool, list[str]]: (success status, list of error messages or success message)
    """
    # https://developers.cloudflare.com/turnstile/tutorials/excluding-turnstile-from-e2e-tests/

    metadata = response.get("metadata", {})
    result_with_testing_key = metadata.get("result_with_testing_key", False)

    if not result_with_testing_key:
        cf_action = response.get("action")
        cf_cdata = response.get("cdata")

        if action is not None and cf_action != action:
            return False, [f"action mismatch: expected '{action}', got '{cf_action}'"]
        if cdata is not None and cf_cdata != cdata:
            return False, [f"cdata mismatch: expected '{cdata}', got '{cf_cdata}'"]

    return True, ["turnstile API verification OK"]


def cf_turnstile_required(
    widget_name: str = None,
    action: Optional[str] = None,
    cdata: Optional[str] = None,
):
    """
    Decorator to require Turnstile CAPTCHA verification on POST requests.

    Args:
        widget_name: The name of the widget to verify against (defaults to "default").
        action: Optional expected action string to verify against the response.
        cdata: Optional expected client data to verify against the response.

    Returns:
        Callable: Decorated view function.
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if request.method == "POST" and not current_app.testing:
                cf_response_token = request.form.get("cf-turnstile-response")
                turnstile = current_app.extensions["turnstile"]

                result, message = turnstile.verify(
                    widget_name=widget_name,
                    token=cf_response_token,
                    client_ip=cf_get_client_ip(),
                    verify_callback=cf_turnstile_additional_verify,
                    action=action,
                    cdata=cdata,
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
