"""
SES Bounce/Complaint Handler — Lambda triggered by SNS.
Manages email suppression list and marks users as unverified.

SNS Topic ARN: arn:aws:sns:us-east-1:ACCOUNT:siteforge-{siteId}-ses-notifications
"""

import json
import logging
from typing import Any
import base64

from lib.db import dynamodb
from lib.response import ok, error

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: Any) -> dict:
    """Handle SNS notification from SES bounce/complaint events."""

    # SNS sends message wrapped in SNS record
    try:
        sns_message = event.get("Records", [{}])[0].get("Sns", {})
        message = json.loads(sns_message.get("Message", "{}"))
    except (KeyError, json.JSONDecodeError, IndexError):
        logger.error(f"Invalid SNS message: {event}")
        return error(400, "Invalid message format")

    event_type = message.get("eventType")
    site_id = sns_message.get("TopicArn", "").split("-")[2]  # Extract from ARN

    if event_type == "Bounce":
        return handle_bounce(message, site_id)
    elif event_type == "Complaint":
        return handle_complaint(message, site_id)
    else:
        logger.info(f"Ignoring event type: {event_type}")
        return ok({"processed": False})


def handle_bounce(message: dict, site_id: str) -> dict:
    """
    Handle bounce event.
    Permanent: mark as unverified.
    Temporary: log for manual review.
    """
    bounce = message.get("bounce", {})
    bounce_type = bounce.get("bounceType")  # Permanent, Temporary, Undetermined

    for recipient in bounce.get("bouncedRecipients", []):
        email = recipient.get("emailAddress")
        status = recipient.get("status")

        if bounce_type == "Permanent":
            # Mark user as unverified — won't receive email notifications
            mark_email_suppressed(site_id, email, "permanent_bounce")
            logger.info(f"Permanent bounce for {email}")
        elif bounce_type == "Temporary":
            logger.warning(f"Temporary bounce for {email}: {status}")

    return ok({"handled_bounces": len(bounce.get("bouncedRecipients", []))})


def handle_complaint(message: dict, site_id: str) -> dict:
    """Handle complaint event — user marked as spam."""
    complaint = message.get("complaint", {})

    for recipient in complaint.get("complainedRecipients", []):
        email = recipient.get("emailAddress")
        mark_email_suppressed(site_id, email, "complaint")
        logger.info(f"Complaint for {email}")

    return ok({"handled_complaints": len(complaint.get("complainedRecipients", []))})


def mark_email_suppressed(site_id: str, email: str, reason: str) -> None:
    """
    Mark email as suppressed in DynamoDB.
    Creates/updates a SuppressedEmail record.
    """
    table = dynamodb.get_table(site_id)

    table.put_item(
        Item={
            "pk": f"SUPPRESSED#{email}",
            "sk": "EMAIL",
            "email": email,
            "reason": reason,
            "suppressedAt": int(__import__("time").time()),
        }
    )


def find_and_suppress_user(site_id: str, email: str) -> None:
    """Find user by email and mark as unverified."""
    table = dynamodb.get_table(site_id)

    # Query users by email (assumes GSI on email)
    response = table.query(
        IndexName="email-index",
        KeyConditionExpression="email = :email",
        ExpressionAttributeValues={":email": email},
    )

    for item in response.get("Items", []):
        table.update_item(
            Key={"pk": item["pk"], "sk": item["sk"]},
            UpdateExpression="SET verified = :verified, updatedAt = :now",
            ExpressionAttributeValues={
                ":verified": False,
                ":now": int(__import__("time").time()),
            },
        )
        logger.info(f"Marked user {item['pk']} as unverified")
