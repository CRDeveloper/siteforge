"""
SiteForge API — Lambda entry point.
Routes all API Gateway v2 HTTP API requests to the correct handler.
"""
import json
import os
import logging
from typing import Any

from middleware.auth import jwt_middleware, is_admin
from middleware.cors import cors_response
from handlers.public import config_handler, services_handler, availability_handler
from handlers.auth import register, login, logout, verify_email, forgot_password, reset_password
from handlers.appointments import (
    list_appointments, create_appointment, cancel_appointment
)
from handlers.admin import (
    admin_appointments, update_appointment, message_user,
    admin_users, admin_stats,
    admin_services, create_service, update_service, delete_service,
    admin_availability, create_availability, delete_availability,
    get_config, update_config,
)
from handlers.uploads import presign_upload
from handlers.me import get_me, update_me
from lib.response import ok, error

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Route table: (method, path_pattern) -> (handler, requires_auth, requires_admin)
ROUTES: list[tuple[str, str, Any, bool, bool]] = [
    # Public
    ("GET",    "/config",                          config_handler,       False, False),
    ("GET",    "/services",                        services_handler,     False, False),
    ("GET",    "/availability",                    availability_handler, False, False),
    # Auth
    ("POST",   "/auth/register",                   register,             False, False),
    ("POST",   "/auth/login",                      login,                False, False),
    ("POST",   "/auth/logout",                     logout,               False, False),
    ("GET",    "/auth/verify",                     verify_email,         False, False),
    ("POST",   "/auth/forgot-password",            forgot_password,      False, False),
    ("POST",   "/auth/reset-password",             reset_password,       False, False),
    # User (auth required)
    ("GET",    "/me",                              get_me,               True,  False),
    ("PATCH",  "/me",                              update_me,            True,  False),
    ("GET",    "/appointments",                    list_appointments,    True,  False),
    ("POST",   "/appointments",                    create_appointment,   True,  False),
    ("DELETE", "/appointments/{id}",               cancel_appointment,   True,  False),
    # Uploads
    ("POST",   "/uploads/presign",                 presign_upload,       True,  False),
    # Admin
    ("GET",    "/admin/appointments",              admin_appointments,   True,  True),
    ("PATCH",  "/admin/appointments/{id}",         update_appointment,   True,  True),
    ("POST",   "/admin/appointments/{id}/message", message_user,         True,  True),
    ("GET",    "/admin/users",                     admin_users,          True,  True),
    ("GET",    "/admin/stats",                     admin_stats,          True,  True),
    ("GET",    "/admin/services",                  admin_services,       True,  True),
    ("POST",   "/admin/services",                  create_service,       True,  True),
    ("PATCH",  "/admin/services/{id}",             update_service,       True,  True),
    ("DELETE", "/admin/services/{id}",             delete_service,       True,  True),
    ("GET",    "/admin/availability",              admin_availability,   True,  True),
    ("POST",   "/admin/availability",              create_availability,  True,  True),
    ("DELETE", "/admin/availability/{id}",         delete_availability,  True,  True),
    ("GET",    "/admin/config",                    get_config,           True,  True),
    ("PATCH",  "/admin/config",                    update_config,        True,  True),
]


def match_route(method: str, path: str):
    """Match incoming method+path against route table, extract path params."""
    for route_method, route_path, handler, auth_required, admin_required in ROUTES:
        if route_method != method:
            continue
        params = _match_path(route_path, path)
        if params is not None:
            return handler, auth_required, admin_required, params
    return None, False, False, {}


def _match_path(pattern: str, path: str) -> dict | None:
    """Match a path against a pattern with {param} segments. Returns params or None."""
    p_parts = pattern.strip("/").split("/")
    r_parts = path.strip("/").split("/")
    if len(p_parts) != len(r_parts):
        return None
    params = {}
    for p, r in zip(p_parts, r_parts):
        if p.startswith("{") and p.endswith("}"):
            params[p[1:-1]] = r
        elif p != r:
            return None
    return params


def handler(event: dict, context: Any) -> dict:
    """Main Lambda handler — routes to sub-handlers."""

    # Handle EventBridge scheduled events
    if event.get("source") == "eventbridge":
        from handlers.scheduler import handle_scheduled
        return handle_scheduled(event)

    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("requestContext", {}).get("http", {}).get("path", "/")

    # Strip /api prefix if present (CloudFront routes /api/* here)
    if path.startswith("/api"):
        path = path[4:] or "/"

    logger.info(f"{method} {path}")

    # OPTIONS — CORS preflight
    if method == "OPTIONS":
        return cors_response()

    route_handler, auth_required, admin_required, path_params = match_route(method, path)

    if route_handler is None:
        return error(404, "Route not found")

    # Build request context
    request = {
        "method": method,
        "path": path,
        "path_params": path_params,
        "query": event.get("queryStringParameters") or {},
        "headers": event.get("headers") or {},
        "body": _parse_body(event),
        "user": None,
        "is_admin": False,
    }

    # Auth middleware
    if auth_required:
        auth_result = jwt_middleware(request)
        if auth_result is not None:
            return auth_result  # 401 response

        if admin_required and not is_admin(request):
            return error(403, "Admin access required")

    try:
        return route_handler(request)
    except Exception as e:
        logger.exception(f"Unhandled error in {route_handler.__name__}: {e}")
        return error(500, "Internal server error")


def _parse_body(event: dict) -> dict:
    body = event.get("body")
    if not body:
        return {}
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return {}
