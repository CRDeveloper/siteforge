"""
Email service — supports Brevo (primary) and AWS SES (scale migration).
Provider is selected via EMAIL_PROVIDER env var from site config.
"""
import boto3
import os
import json
import logging
import requests
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_brevo_api_key() -> str:
    ssm = boto3.client("ssm")
    param_name = os.environ["BREVO_API_KEY_PARAM"]
    resp = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return resp["Parameter"]["Value"]


def send_email(
    template_name: str,
    to_email: str,
    to_name: str,
    params: dict,
    lang: str = "en",
) -> bool:
    """
    Send a transactional email.
    template_name maps to a template ID stored in SSM or site config.
    """
    provider = os.environ.get("EMAIL_PROVIDER", "brevo")

    if provider == "brevo":
        return _send_brevo(template_name, to_email, to_name, params, lang)
    elif provider == "ses":
        return _send_ses(template_name, to_email, to_name, params, lang)
    else:
        logger.error(f"Unknown email provider: {provider}")
        return False


def _get_template_id(template_name: str) -> Optional[int]:
    """Fetch Brevo template ID from SSM site config."""
    try:
        ssm = boto3.client("ssm")
        site_id = os.environ["SITE_ID"]
        resp = ssm.get_parameter(Name=f"/siteforge/{site_id}/config")
        config = json.loads(resp["Parameter"]["Value"])
        return config["email"]["templates"].get(template_name)
    except Exception as e:
        logger.error(f"Could not fetch template ID for {template_name}: {e}")
        return None


def _send_brevo(
    template_name: str,
    to_email: str,
    to_name: str,
    params: dict,
    lang: str,
) -> bool:
    template_id = _get_template_id(template_name)
    if not template_id:
        logger.error(f"No template ID found for: {template_name}")
        return False

    api_key = _get_brevo_api_key()
    sender_email = os.environ["SENDER_EMAIL"]
    sender_name = os.environ["SENDER_NAME"]

    payload = {
        "to": [{"email": to_email, "name": to_name}],
        "templateId": template_id,
        "params": params,
        "sender": {"email": sender_email, "name": sender_name},
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        if resp.status_code == 201:
            logger.info(f"Email sent via Brevo: {template_name} → {to_email}")
            return True
        else:
            logger.error(f"Brevo error {resp.status_code}: {resp.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"Brevo request failed: {e}")
        return False


def _send_ses(
    template_name: str,
    to_email: str,
    to_name: str,
    params: dict,
    lang: str,
) -> bool:
    """SES fallback — uses SES templates (must be pre-created in AWS)."""
    ses = boto3.client("ses")
    sender = f"{os.environ['SENDER_NAME']} <{os.environ['SENDER_EMAIL']}>"

    try:
        ses.send_templated_email(
            Source=sender,
            Destination={"ToAddresses": [f"{to_name} <{to_email}>"]},
            Template=f"siteforge-{template_name}",
            TemplateData=json.dumps(params),
        )
        logger.info(f"Email sent via SES: {template_name} → {to_email}")
        return True
    except Exception as e:
        logger.error(f"SES send failed: {e}")
        return False


def sync_contact_to_brevo(
    email: str,
    first_name: str,
    last_name: str,
    phone: str = None,
    list_id: int = None,
) -> bool:
    """Sync a new user registration to Brevo contacts list."""
    try:
        api_key = _get_brevo_api_key()
        payload = {
            "email": email,
            "attributes": {
                "FIRSTNAME": first_name,
                "LASTNAME": last_name,
            },
            "updateEnabled": True,
        }
        if phone:
            payload["attributes"]["SMS"] = phone
        if list_id:
            payload["listIds"] = [list_id]

        resp = requests.post(
            "https://api.brevo.com/v3/contacts",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=5,
        )
        success = resp.status_code in (201, 204)
        if not success:
            logger.warning(f"Brevo contact sync failed: {resp.status_code} {resp.text}")
        return success
    except Exception as e:
        logger.error(f"Brevo contact sync error: {e}")
        return False
