"""
Appointment handlers (user-facing).
GET /appointments, POST /appointments, DELETE /appointments/{id}
"""
import uuid
import time
import os
import logging
from datetime import datetime, timezone, date as date_type

from lib.db import (
    put_item, get_item, update_item, get_user_appointments,
    get_appointment, get_available_slots, query,
)
from lib.email import send_email
from lib.response import ok, created, error

logger = logging.getLogger(__name__)


def list_appointments(request: dict) -> dict:
    """GET /appointments — current user's appointments."""
    user_id = request["user"]["userId"]
    try:
        # Get appointment references from user partition
        refs = get_user_appointments(user_id)
        appt_ids = [r["SK"].replace("APPT#", "") for r in refs]

        # Fetch full appointment details
        appointments = []
        for appt_id in appt_ids:
            appt = get_appointment(appt_id)
            if appt:
                appointments.append(_safe_appt(appt))

        # Sort upcoming first
        appointments.sort(key=lambda a: (a["date"], a["time"]))
        return ok({"appointments": appointments})
    except Exception as e:
        logger.error(f"list_appointments error: {e}")
        return error(500, "Could not load appointments")


def create_appointment(request: dict) -> dict:
    """POST /appointments — book a new appointment."""
    user = request["user"]
    body = request["body"]

    service_id = body.get("serviceId", "").strip()
    date_str = body.get("date", "").strip()
    time_str = body.get("time", "").strip()
    notes = body.get("notes", "").strip()[:500]
    attachment_key = body.get("attachmentKey", "").strip()

    # Validate required fields
    if not all([service_id, date_str, time_str]):
        return error(400, "serviceId, date, and time are required")

    # Validate date format and future date
    try:
        appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if appt_date < date_type.today():
            return error(400, "Appointment date must be in the future")
    except ValueError:
        return error(400, "Invalid date format. Use YYYY-MM-DD")

    # Validate time format
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return error(400, "Invalid time format. Use HH:MM")

    # Check window
    window_days = int(os.environ.get("CANCELLATION_HOURS", "30"))
    max_date = date_type.today().toordinal() + window_days
    if appt_date.toordinal() > max_date:
        return error(400, f"Appointments can only be booked up to {window_days} days in advance")

    # Check slot is still available
    booked = get_item(f"BOOKED#{date_str}", f"TIME#{time_str}")
    if booked:
        return error(409, "This time slot is no longer available. Please choose another.")

    # Fetch service info
    from lib.db import get_item as db_get
    service = db_get(f"SERVICE#{service_id}", "DETAIL")
    if not service or not service.get("active"):
        return error(404, "Service not found")

    now = _now()
    appt_id = str(uuid.uuid4())

    # Write appointment detail record
    appt = {
        "PK": f"APPT#{appt_id}",
        "SK": "DETAIL",
        "apptId": appt_id,
        "userId": user["userId"],
        "userEmail": user["email"],
        "userName": user.get("firstName", ""),
        "serviceId": service_id,
        "serviceName": service.get("name", {}),
        "date": date_str,
        "time": time_str,
        "status": "pending",
        "notes": notes,
        "attachmentKey": attachment_key,
        "adminMessage": "",
        "reminderSent": False,
        "createdAt": _iso(now),
        "updatedAt": _iso(now),
        # GSI1 — admin can query by status + date
        "GSI1PK": "STATUS#pending",
        "GSI1SK": f"DATE#{date_str}",
    }
    put_item(appt)

    # Write user appointment index
    put_item({
        "PK": f"USER#{user['userId']}",
        "SK": f"APPT#{appt_id}",
        "apptId": appt_id,
        "date": date_str,
        "time": time_str,
        "status": "pending",
    })

    # Reserve the slot
    put_item({
        "PK": f"BOOKED#{date_str}",
        "SK": f"TIME#{time_str}",
        "apptId": appt_id,
    })

    lang = user.get("lang", os.environ.get("DEFAULT_LANG", "en"))
    service_name = service["name"].get(lang) or service["name"].get("en", "")

    # Email: confirmation to user
    send_email(
        template_name="appointmentAdminAlert",
        to_email=os.environ["ADMIN_EMAIL"],
        to_name=os.environ.get("SENDER_NAME", "Admin"),
        params={
            "userName": user.get("firstName", user["email"]),
            "userEmail": user["email"],
            "serviceName": service_name,
            "date": date_str,
            "time": time_str,
            "notes": notes or "None",
            "dashboardUrl": f"https://{os.environ['DOMAIN']}/admin/appointments/{appt_id}",
        },
    )

    # Email: alert to admin
    send_email(
        template_name="appointmentConfirmed",
        to_email=user["email"],
        to_name=user.get("firstName", ""),
        params={
            "firstName": user.get("firstName", ""),
            "serviceName": service_name,
            "date": date_str,
            "time": time_str,
            "notes": notes or "",
            "appointmentUrl": f"https://{os.environ['DOMAIN']}/appointments/{appt_id}",
        },
    )

    return created({"appointment": _safe_appt(appt)})


def cancel_appointment(request: dict) -> dict:
    """DELETE /appointments/{id} — user cancels their own appointment."""
    user_id = request["user"]["userId"]
    appt_id = request["path_params"].get("id", "")

    appt = get_appointment(appt_id)
    if not appt:
        return error(404, "Appointment not found")

    if appt["userId"] != user_id:
        return error(403, "Not your appointment")

    if appt["status"] in ("cancelled", "declined"):
        return error(400, "Appointment is already cancelled")

    # Check cancellation window
    cancellation_hours = int(os.environ.get("CANCELLATION_HOURS", "24"))
    appt_datetime_str = f"{appt['date']} {appt['time']}"
    appt_dt = datetime.strptime(appt_datetime_str, "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    )
    hours_until = (appt_dt - datetime.now(timezone.utc)).total_seconds() / 3600
    if hours_until < cancellation_hours:
        return error(
            400,
            f"Appointments must be cancelled at least {cancellation_hours} hours in advance. "
            f"Please call us to cancel.",
        )

    now = _now()
    update_item(f"APPT#{appt_id}", "DETAIL", {
        "status": "cancelled",
        "GSI1PK": "STATUS#cancelled",
        "updatedAt": _iso(now),
    })
    update_item(f"USER#{user_id}", f"APPT#{appt_id}", {"status": "cancelled"})

    # Free up the slot
    from lib.db import delete_item
    delete_item(f"BOOKED#{appt['date']}", f"TIME#{appt['time']}")

    # Notify admin
    send_email(
        template_name="appointmentCancelled",
        to_email=os.environ["ADMIN_EMAIL"],
        to_name=os.environ.get("SENDER_NAME", "Admin"),
        params={
            "userName": request["user"].get("firstName", user_id),
            "date": appt["date"],
            "time": appt["time"],
            "serviceName": appt.get("serviceName", {}).get("en", ""),
        },
    )

    return ok({"message": "Appointment cancelled"})


def _safe_appt(appt: dict) -> dict:
    """Strip internal DynamoDB keys before returning to client."""
    exclude = {"PK", "SK", "GSI1PK", "GSI1SK", "passwordHash"}
    return {k: v for k, v in appt.items() if k not in exclude}


def _now() -> int:
    return int(time.time())


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
