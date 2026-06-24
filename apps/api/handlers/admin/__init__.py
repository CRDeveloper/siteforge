"""
Admin handlers — all require admin JWT.
"""
import uuid
import time
import os
import logging
from datetime import datetime, timezone

from lib.db import (
    put_item, get_item, update_item, delete_item, query,
    get_appointment, get_site_config, scan_prefix,
)
from lib.email import send_email
from lib.response import ok, created, error

logger = logging.getLogger(__name__)


# ── Appointments ──────────────────────────────────────────────────────────────

def admin_appointments(request: dict) -> dict:
    """GET /admin/appointments?status=pending&date=2025-07-01"""
    status = request["query"].get("status", "pending")
    date_from = request["query"].get("date", "")

    valid_statuses = {"pending", "accepted", "declined", "rescheduled", "cancelled"}
    if status not in valid_statuses and status != "all":
        return error(400, f"status must be one of: {', '.join(valid_statuses)}, all")

    try:
        if status == "all":
            appointments = []
            for s in valid_statuses:
                appointments.extend(
                    query(pk=f"STATUS#{s}", sk_prefix=f"DATE#{date_from}" if date_from else "DATE#", index="GSI1")
                )
        else:
            appointments = query(
                pk=f"STATUS#{status}",
                sk_prefix=f"DATE#{date_from}" if date_from else "DATE#",
                index="GSI1",
            )

        # Fetch full records (GSI returns projection only)
        full_appts = []
        for ref in appointments:
            appt_id = ref.get("apptId") or ref["PK"].replace("APPT#", "")
            full = get_appointment(appt_id)
            if full:
                full_appts.append(_safe(full))

        full_appts.sort(key=lambda a: (a.get("date", ""), a.get("time", "")))
        return ok({"appointments": full_appts, "count": len(full_appts)})
    except Exception as e:
        logger.error(f"admin_appointments error: {e}")
        return error(500, "Could not load appointments")


def update_appointment(request: dict) -> dict:
    """
    PATCH /admin/appointments/{id}
    body: { status, newDate?, newTime?, adminMessage? }
    """
    appt_id = request["path_params"].get("id", "")
    body = request["body"]

    appt = get_appointment(appt_id)
    if not appt:
        return error(404, "Appointment not found")

    new_status = body.get("status", "").strip()
    valid = {"accepted", "declined", "rescheduled"}
    if new_status not in valid:
        return error(400, f"status must be one of: {', '.join(valid)}")

    updates = {
        "status": new_status,
        "GSI1PK": f"STATUS#{new_status}",
        "adminMessage": body.get("adminMessage", "").strip()[:500],
        "updatedAt": _iso(_now()),
    }

    if new_status == "rescheduled":
        new_date = body.get("newDate", "").strip()
        new_time = body.get("newTime", "").strip()
        if not new_date or not new_time:
            return error(400, "newDate and newTime are required for rescheduled status")
        # Free old slot, reserve new one
        delete_item(f"BOOKED#{appt['date']}", f"TIME#{appt['time']}")
        put_item({"PK": f"BOOKED#{new_date}", "SK": f"TIME#{new_time}", "apptId": appt_id})
        updates["date"] = new_date
        updates["time"] = new_time
        updates["GSI1SK"] = f"DATE#{new_date}"

    update_item(f"APPT#{appt_id}", "DETAIL", updates)
    # Update user index
    update_item(f"USER#{appt['userId']}", f"APPT#{appt_id}", {"status": new_status})

    lang = os.environ.get("DEFAULT_LANG", "en")
    service_name = appt.get("serviceName", {})
    service_name = service_name.get(lang) if isinstance(service_name, dict) else str(service_name)

    template_map = {
        "accepted": "appointmentConfirmed",
        "declined": "appointmentDeclined",
        "rescheduled": "appointmentRescheduled",
    }
    send_email(
        template_name=template_map[new_status],
        to_email=appt["userEmail"],
        to_name=appt.get("userName", ""),
        params={
            "firstName": appt.get("userName", ""),
            "serviceName": service_name,
            "date": updates.get("date", appt["date"]),
            "time": updates.get("time", appt["time"]),
            "adminMessage": updates["adminMessage"],
            "appointmentUrl": f"https://{os.environ['DOMAIN']}/appointments/{appt_id}",
        },
    )

    return ok({"message": f"Appointment {new_status}", "apptId": appt_id})


def message_user(request: dict) -> dict:
    """POST /admin/appointments/{id}/message"""
    appt_id = request["path_params"].get("id", "")
    message = (request["body"].get("message") or "").strip()[:1000]

    if not message:
        return error(400, "message is required")

    appt = get_appointment(appt_id)
    if not appt:
        return error(404, "Appointment not found")

    update_item(f"APPT#{appt_id}", "DETAIL", {
        "adminMessage": message,
        "updatedAt": _iso(_now()),
    })

    send_email(
        template_name="appointmentAdminAlert",
        to_email=appt["userEmail"],
        to_name=appt.get("userName", ""),
        params={
            "firstName": appt.get("userName", ""),
            "adminMessage": message,
            "appointmentUrl": f"https://{os.environ['DOMAIN']}/appointments/{appt_id}",
        },
    )
    return ok({"message": "Message sent"})


# ── Users ─────────────────────────────────────────────────────────────────────

def admin_users(request: dict) -> dict:
    """GET /admin/users"""
    try:
        users = scan_prefix("USER#", limit=200)
        users = [u for u in users if u["SK"] == "PROFILE"]
        safe_users = [_safe_user(u) for u in users]
        safe_users.sort(key=lambda u: u.get("createdAt", ""), reverse=True)
        return ok({"users": safe_users, "count": len(safe_users)})
    except Exception as e:
        logger.error(f"admin_users error: {e}")
        return error(500, "Could not load users")


# ── Stats ─────────────────────────────────────────────────────────────────────

def admin_stats(request: dict) -> dict:
    """GET /admin/stats — dashboard summary metrics."""
    try:
        from datetime import date
        today = date.today().isoformat()
        week_start = date.fromordinal(date.today().toordinal() - date.today().weekday()).isoformat()

        pending = query(pk="STATUS#pending", sk_prefix="DATE#", index="GSI1")
        accepted = query(pk="STATUS#accepted", sk_prefix=f"DATE#{week_start}", index="GSI1")
        today_appts = query(pk="STATUS#accepted", sk_prefix=f"DATE#{today}", index="GSI1")

        users = scan_prefix("USER#", limit=500)
        user_count = len([u for u in users if u.get("SK") == "PROFILE"])

        return ok({
            "stats": {
                "pendingAppointments": len(pending),
                "acceptedThisWeek": len(accepted),
                "todayAppointments": len(today_appts),
                "totalUsers": user_count,
            }
        })
    except Exception as e:
        logger.error(f"admin_stats error: {e}")
        return error(500, "Could not load stats")


# ── Services ──────────────────────────────────────────────────────────────────

def admin_services(request: dict) -> dict:
    """GET /admin/services"""
    services = scan_prefix("SERVICE#")
    return ok({"services": [_safe(s) for s in services]})


def create_service(request: dict) -> dict:
    """POST /admin/services"""
    body = request["body"]
    name = body.get("name", {})
    description = body.get("description", {})
    duration = int(body.get("durationMinutes", 50))

    if not name.get("en"):
        return error(400, "name.en is required")

    service_id = str(uuid.uuid4())
    service = {
        "PK": f"SERVICE#{service_id}",
        "SK": "DETAIL",
        "serviceId": service_id,
        "name": name,
        "description": description,
        "durationMinutes": duration,
        "active": True,
        "createdAt": _iso(_now()),
    }
    put_item(service)
    return created({"service": _safe(service)})


def update_service(request: dict) -> dict:
    """PATCH /admin/services/{id}"""
    service_id = request["path_params"].get("id", "")
    body = request["body"]
    updates = {}
    for field in ("name", "description", "durationMinutes", "active"):
        if field in body:
            updates[field] = body[field]
    updates["updatedAt"] = _iso(_now())
    updated = update_item(f"SERVICE#{service_id}", "DETAIL", updates)
    return ok({"service": _safe(updated)})


def delete_service(request: dict) -> dict:
    """DELETE /admin/services/{id} — soft delete (sets active=False)."""
    service_id = request["path_params"].get("id", "")
    update_item(f"SERVICE#{service_id}", "DETAIL", {"active": False, "updatedAt": _iso(_now())})
    return ok({"message": "Service deactivated"})


# ── Availability ──────────────────────────────────────────────────────────────

def admin_availability(request: dict) -> dict:
    """GET /admin/availability?date=YYYY-MM-DD"""
    date_str = request["query"].get("date", "")
    if not date_str:
        return error(400, "date is required")
    slots = query(pk=f"SLOT#{date_str}", sk_prefix="TIME#")
    return ok({"date": date_str, "slots": [_safe(s) for s in slots]})


def create_availability(request: dict) -> dict:
    """POST /admin/availability — add time slots for a date."""
    body = request["body"]
    date_str = body.get("date", "").strip()
    times = body.get("times", [])  # e.g. ["09:00","10:00","11:00"]

    if not date_str or not times:
        return error(400, "date and times[] are required")

    created_slots = []
    for t in times:
        slot = {
            "PK": f"SLOT#{date_str}",
            "SK": f"TIME#{t}",
            "date": date_str,
            "time": t,
            "label": t,
        }
        put_item(slot)
        created_slots.append(slot)

    return created({"slots": created_slots, "count": len(created_slots)})


def delete_availability(request: dict) -> dict:
    """DELETE /admin/availability/{id} — id format: DATE_TIME e.g. 2025-07-15_10:00"""
    slot_id = request["path_params"].get("id", "")
    try:
        date_str, time_str = slot_id.split("_", 1)
    except ValueError:
        return error(400, "Invalid slot id format. Use YYYY-MM-DD_HH:MM")
    delete_item(f"SLOT#{date_str}", f"TIME#{time_str}")
    return ok({"message": "Slot removed"})


# ── Site Config ───────────────────────────────────────────────────────────────

def get_config(request: dict) -> dict:
    """GET /admin/config"""
    config = get_site_config()
    return ok({"config": config})


def update_config(request: dict) -> dict:
    """PATCH /admin/config — update theme, content, settings."""
    body = request["body"]
    allowed = {"theme", "content", "appointments", "siteName", "tagline"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return error(400, "No valid fields to update")
    updates["updatedAt"] = _iso(_now())
    updated = update_item("CONFIG#SITE", "SETTINGS", updates)
    return ok({"config": updated})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe(item: dict) -> dict:
    exclude = {"PK", "SK", "GSI1PK", "GSI1SK"}
    return {k: v for k, v in item.items() if k not in exclude}


def _safe_user(user: dict) -> dict:
    exclude = {"PK", "SK", "GSI1PK", "GSI1SK", "passwordHash",
               "verifyTokenHash", "verifyTokenExpiry",
               "resetTokenHash", "resetTokenExpiry"}
    return {k: v for k, v in user.items() if k not in exclude}


def _now() -> int:
    return int(time.time())


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
