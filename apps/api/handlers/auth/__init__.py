"""
Auth handlers: register, login, logout, verify email, password reset.
"""
import uuid
import time
import hashlib
import os
import logging
import re
import secrets

import bcrypt

from lib.db import put_item, get_user_by_email, get_item, update_item, get_user
from lib.email import send_email, sync_contact_to_brevo
from lib.response import ok, created, error, set_cookie, clear_cookie
from middleware.auth import create_token

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Register ──────────────────────────────────────────────────────────────────

def register(request: dict) -> dict:
    body = request["body"]
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    first_name = (body.get("firstName") or "").strip()
    last_name = (body.get("lastName") or "").strip()
    phone = (body.get("phone") or "").strip()

    # Validate
    if not EMAIL_RE.match(email):
        return error(400, "Invalid email address")
    if len(password) < 8:
        return error(400, "Password must be at least 8 characters")
    if not first_name:
        return error(400, "First name is required")

    # Check duplicate
    existing = get_user_by_email(email)
    if existing:
        return error(409, "An account with this email already exists")

    # Hash password
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Verification token
    verify_token = secrets.token_urlsafe(32)
    verify_token_hash = hashlib.sha256(verify_token.encode()).hexdigest()

    user_id = str(uuid.uuid4())
    now = _now()

    user = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "userId": user_id,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "phone": phone,
        "passwordHash": pw_hash,
        "verified": False,
        "verifyTokenHash": verify_token_hash,
        "verifyTokenExpiry": now + 86400,  # 24h
        "role": "user",
        "createdAt": _iso(now),
        "updatedAt": _iso(now),
        # GSI2 — email lookup
        "email": email,
    }
    put_item(user)

    # Send verification email
    domain = os.environ["DOMAIN"]
    verify_url = f"https://{domain}/auth/verify?token={verify_token}&email={email}"
    send_email(
        template_name="verifyEmail",
        to_email=email,
        to_name=f"{first_name} {last_name}",
        params={
            "firstName": first_name,
            "verificationUrl": verify_url,
            "siteName": os.environ.get("SENDER_NAME", ""),
        },
    )

    # Sync to Brevo contacts (non-blocking)
    try:
        sync_contact_to_brevo(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone or None,
        )
    except Exception as e:
        logger.warning(f"Brevo contact sync failed (non-fatal): {e}")

    return created({"message": "Account created. Please check your email to verify."})


# ── Verify Email ──────────────────────────────────────────────────────────────

def verify_email(request: dict) -> dict:
    token = request["query"].get("token", "")
    email = (request["query"].get("email") or "").lower()

    if not token or not email:
        return error(400, "Missing token or email")

    user = get_user_by_email(email)
    if not user:
        return error(404, "User not found")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if user.get("verifyTokenHash") != token_hash:
        return error(400, "Invalid verification token")

    if int(time.time()) > user.get("verifyTokenExpiry", 0):
        return error(400, "Verification token has expired. Please request a new one.")

    update_item(
        user["PK"], "PROFILE",
        {
            "verified": True,
            "verifyTokenHash": None,
            "verifyTokenExpiry": None,
            "updatedAt": _iso(_now()),
        },
    )
    return ok({"message": "Email verified. You can now log in."})


# ── Login ─────────────────────────────────────────────────────────────────────

def login(request: dict) -> dict:
    body = request["body"]
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return error(400, "Email and password are required")

    user = get_user_by_email(email)
    if not user:
        return error(401, "Invalid email or password")

    if not bcrypt.checkpw(password.encode(), user["passwordHash"].encode()):
        return error(401, "Invalid email or password")

    if not user.get("verified"):
        return error(403, "Please verify your email before logging in")

    token = create_token({
        "userId": user["userId"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "firstName": user.get("firstName"),
    })

    return set_cookie(
        data={
            "userId": user["userId"],
            "firstName": user.get("firstName"),
            "role": user.get("role", "user"),
        },
        cookie_name="sf_token",
        cookie_value=token,
    )


# ── Logout ────────────────────────────────────────────────────────────────────

def logout(request: dict) -> dict:
    return clear_cookie("sf_token")


# ── Forgot Password ───────────────────────────────────────────────────────────

def forgot_password(request: dict) -> dict:
    email = (request["body"].get("email") or "").strip().lower()
    if not EMAIL_RE.match(email):
        return error(400, "Invalid email address")

    user = get_user_by_email(email)
    # Always return success to prevent email enumeration
    if not user:
        return ok({"message": "If an account exists, a reset link has been sent."})

    reset_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    now = _now()

    update_item(
        user["PK"], "PROFILE",
        {
            "resetTokenHash": token_hash,
            "resetTokenExpiry": now + 3600,  # 1 hour
            "updatedAt": _iso(now),
        },
    )

    domain = os.environ["DOMAIN"]
    reset_url = f"https://{domain}/auth/reset-password?token={reset_token}&email={email}"
    send_email(
        template_name="passwordReset",
        to_email=email,
        to_name=f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
        params={
            "firstName": user.get("firstName", ""),
            "resetUrl": reset_url,
            "siteName": os.environ.get("SENDER_NAME", ""),
        },
    )

    return ok({"message": "If an account exists, a reset link has been sent."})


# ── Reset Password ────────────────────────────────────────────────────────────

def reset_password(request: dict) -> dict:
    body = request["body"]
    token = body.get("token") or ""
    email = (body.get("email") or "").strip().lower()
    new_password = body.get("password") or ""

    if len(new_password) < 8:
        return error(400, "Password must be at least 8 characters")

    user = get_user_by_email(email)
    if not user:
        return error(400, "Invalid reset link")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if user.get("resetTokenHash") != token_hash:
        return error(400, "Invalid or expired reset link")

    if int(time.time()) > user.get("resetTokenExpiry", 0):
        return error(400, "Reset link has expired. Please request a new one.")

    pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    update_item(
        user["PK"], "PROFILE",
        {
            "passwordHash": pw_hash,
            "resetTokenHash": None,
            "resetTokenExpiry": None,
            "updatedAt": _iso(_now()),
        },
    )

    return ok({"message": "Password updated. You can now log in."})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> int:
    return int(time.time())


def _iso(ts: int) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
