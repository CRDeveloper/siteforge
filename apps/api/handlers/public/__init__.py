"""
Public handlers — no auth required.
GET /config, GET /services, GET /availability
"""
import os
import json
import logging
import boto3
from functools import lru_cache

from lib.db import get_services, get_available_slots, get_site_config
from lib.response import ok, error

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_site_config_from_ssm() -> dict:
    """Load full site config from SSM (cached per Lambda container)."""
    ssm = boto3.client("ssm")
    site_id = os.environ["SITE_ID"]
    resp = ssm.get_parameter(Name=f"/siteforge/{site_id}/config")
    return json.loads(resp["Parameter"]["Value"])


def config_handler(request: dict) -> dict:
    """
    GET /config
    Returns public site config: theme, langs, content, services list.
    Used by Next.js at build time and runtime for theming + i18n.
    """
    try:
        config = _load_site_config_from_ssm()
        # Return only public-safe fields (strip email secrets etc.)
        public_config = {
            "siteId": config["siteId"],
            "siteName": config["siteName"],
            "tagline": config.get("tagline", {}),
            "defaultLang": config.get("defaultLang", "en"),
            "supportedLangs": config.get("supportedLangs", ["en"]),
            "theme": config.get("theme", {}),
            "content": config.get("content", {}),
            "seo": config.get("seo", {}),
            "appointments": {
                "windowDays": config["appointments"]["windowDays"],
                "cancellationHours": config["appointments"]["cancellationHours"],
            },
        }
        return ok({"config": public_config})
    except Exception as e:
        logger.error(f"Config load error: {e}")
        return error(500, "Could not load site configuration")


def services_handler(request: dict) -> dict:
    """
    GET /services
    Returns all active services.
    """
    try:
        services = get_services(active_only=True)
        # Sort by name for consistent ordering
        services.sort(key=lambda s: s.get("name", {}).get("en", ""))
        return ok({"services": services})
    except Exception as e:
        logger.error(f"Services load error: {e}")
        return error(500, "Could not load services")


def availability_handler(request: dict) -> dict:
    """
    GET /availability?date=YYYY-MM-DD
    Returns available time slots for a given date.
    Filters out slots already booked.
    """
    date = request["query"].get("date", "")
    if not date or len(date) != 10:
        return error(400, "date parameter required (YYYY-MM-DD)")

    try:
        from datetime import date as date_type, datetime
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")

        # Don't allow past dates
        if date < date_type.today().isoformat():
            return ok({"date": date, "slots": []})

        slots = get_available_slots(date)

        # Filter out already-booked slots
        from lib.db import query
        booked = query(pk=f"BOOKED#{date}", sk_prefix="TIME#")
        booked_times = {b["SK"].replace("TIME#", "") for b in booked}

        available = [
            s for s in slots
            if s["SK"].replace("TIME#", "") not in booked_times
        ]

        return ok({
            "date": date,
            "slots": [
                {"time": s["SK"].replace("TIME#", ""), "label": s.get("label", "")}
                for s in available
            ],
        })
    except ValueError:
        return error(400, "Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Availability error: {e}")
        return error(500, "Could not load availability")
