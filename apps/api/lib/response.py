"""Standard HTTP response helpers for Lambda → API Gateway."""
import json
import os

DOMAIN = os.environ.get("DOMAIN", "*")
ALLOWED_ORIGIN = f"https://{DOMAIN}"


def _response(status: int, body: dict, extra_headers: dict = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Credentials": "true",
    }
    if extra_headers:
        headers.update(extra_headers)
    return {
        "statusCode": status,
        "headers": headers,
        "body": json.dumps(body, default=str),
    }


def ok(data: dict = None, status: int = 200) -> dict:
    return _response(status, {"ok": True, **(data or {})})


def created(data: dict = None) -> dict:
    return _response(201, {"ok": True, **(data or {})})


def error(status: int, message: str, details: dict = None) -> dict:
    body = {"ok": False, "error": message}
    if details:
        body["details"] = details
    return _response(status, body)


def set_cookie(data: dict, cookie_name: str, cookie_value: str,
               max_age: int = 86400 * 7) -> dict:
    """Return ok() response with a Set-Cookie header."""
    domain = os.environ.get("DOMAIN", "")
    cookie = (
        f"{cookie_name}={cookie_value}; "
        f"HttpOnly; Secure; SameSite=Strict; "
        f"Max-Age={max_age}; Path=/; Domain={domain}"
    )
    return _response(200, {"ok": True, **data}, {"Set-Cookie": cookie})


def clear_cookie(cookie_name: str) -> dict:
    domain = os.environ.get("DOMAIN", "")
    cookie = (
        f"{cookie_name}=; HttpOnly; Secure; SameSite=Strict; "
        f"Max-Age=0; Path=/; Domain={domain}"
    )
    return _response(200, {"ok": True}, {"Set-Cookie": cookie})
