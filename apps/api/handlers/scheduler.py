"""
Scheduler handler — triggered by EventBridge daily cron.
Sends 24h appointment reminders.
"""
import os
import logging
from datetime import date, timedelta

from lib.db import query, update_item
from lib.email import send_email

logger = logging.getLogger(__name__)


def handle_scheduled(event: dict) -> dict:
    action = event.get("action")
    if action == "send_reminders":
        return _send_reminders()
    logger.warning(f"Unknown scheduled action: {action}")
    return {"ok": False}


def _send_reminders() -> dict:
    reminder_hours = int(os.environ.get("REMINDER_HOURS", "24"))
    # Calculate target date (appointments happening ~24h from now)
    target_date = (date.today() + timedelta(hours=reminder_hours)).isoformat()

    logger.info(f"Sending reminders for appointments on {target_date}")

    appointments = query(
        pk="STATUS#accepted",
        sk_prefix=f"DATE#{target_date}",
        index="GSI1",
    )

    sent = 0
    for ref in appointments:
        appt_id = ref.get("apptId") or ref["PK"].replace("APPT#", "")
        from lib.db import get_appointment
        appt = get_appointment(appt_id)

        if not appt or appt.get("reminderSent"):
            continue

        lang = os.environ.get("DEFAULT_LANG", "en")
        service_name = appt.get("serviceName", {})
        if isinstance(service_name, dict):
            service_name = service_name.get(lang) or service_name.get("en", "")

        success = send_email(
            template_name="appointmentReminder",
            to_email=appt["userEmail"],
            to_name=appt.get("userName", ""),
            params={
                "firstName": appt.get("userName", ""),
                "serviceName": service_name,
                "date": appt["date"],
                "time": appt["time"],
                "appointmentUrl": f"https://{os.environ['DOMAIN']}/appointments/{appt_id}",
            },
        )

        if success:
            update_item(f"APPT#{appt_id}", "DETAIL", {"reminderSent": True})
            sent += 1

    logger.info(f"Reminders sent: {sent}/{len(appointments)}")
    return {"ok": True, "remindersSent": sent}
