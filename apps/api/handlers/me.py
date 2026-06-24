"""GET /me, PATCH /me — user profile."""
import time
import logging
from datetime import datetime, timezone

from lib.db import get_user, update_item
from lib.response import ok, error

logger = logging.getLogger(__name__)


def get_me(request: dict) -> dict:
    user_id = request["user"]["userId"]
    user = get_user(user_id)
    if not user:
        return error(404, "User not found")
    return ok({"user": _safe(user)})


def update_me(request: dict) -> dict:
    user_id = request["user"]["userId"]
    body = request["body"]
    allowed = {"firstName", "lastName", "phone", "lang"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return error(400, "No valid fields to update")
    updates["updatedAt"] = datetime.fromtimestamp(
        int(time.time()), tz=timezone.utc
    ).isoformat()
    updated = update_item(f"USER#{user_id}", "PROFILE", updates)
    return ok({"user": _safe(updated)})


def _safe(user: dict) -> dict:
    exclude = {"PK", "SK", "passwordHash", "verifyTokenHash",
               "verifyTokenExpiry", "resetTokenHash", "resetTokenExpiry"}
    return {k: v for k, v in user.items() if k not in exclude}
