"""
JWT authentication middleware.
Validates Bearer tokens from Authorization header or session cookie.
"""
import os
import logging
import boto3
from functools import lru_cache
import jwt  # PyJWT

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days


@lru_cache(maxsize=1)
def _get_jwt_secret() -> str:
    ssm = boto3.client("ssm")
    site_id = os.environ["SITE_ID"]
    resp = ssm.get_parameter(
        Name=f"/siteforge/{site_id}/jwt_secret",
        WithDecryption=True,
    )
    return resp["Parameter"]["Value"]


def create_token(payload: dict) -> str:
    """Create a signed JWT."""
    import time
    data = {
        **payload,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
    }
    return jwt.encode(data, _get_jwt_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns payload or None."""
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.info("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.info(f"Invalid JWT: {e}")
        return None


def jwt_middleware(request: dict) -> dict | None:
    """
    Extract + validate JWT from Authorization header or cookie.
    Mutates request['user'] on success.
    Returns 401 response dict on failure, None on success.
    """
    from lib.response import error

    token = _extract_token(request)
    if not token:
        return error(401, "Authentication required")

    payload = decode_token(token)
    if not payload:
        return error(401, "Invalid or expired token")

    request["user"] = payload
    request["is_admin"] = payload.get("role") == "admin"
    return None  # success — continue to handler


def is_admin(request: dict) -> bool:
    return request.get("is_admin", False)


def _extract_token(request: dict) -> str | None:
    """Try Authorization header first, then cookie."""
    auth_header = request.get("headers", {}).get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    # Try cookie
    cookie_header = request.get("headers", {}).get("cookie", "")
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("sf_token="):
            return part[9:]

    return None
