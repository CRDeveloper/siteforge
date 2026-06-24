"""
DynamoDB single-table helper.
Wraps boto3 with typed helpers for SiteForge entity patterns.
"""
import boto3
import os
import logging
from typing import Any, Optional
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger(__name__)

_resource = None


def get_table():
    """Lazy singleton DynamoDB table resource."""
    global _resource
    if _resource is None:
        dynamodb = boto3.resource("dynamodb")
        _resource = dynamodb.Table(os.environ["TABLE_NAME"])
    return _resource


# ── Generic CRUD ─────────────────────────────────────────────────────────────

def put_item(item: dict) -> dict:
    table = get_table()
    table.put_item(Item=item)
    return item


def get_item(pk: str, sk: str) -> Optional[dict]:
    table = get_table()
    resp = table.get_item(Key={"PK": pk, "SK": sk})
    return resp.get("Item")


def update_item(pk: str, sk: str, updates: dict) -> dict:
    """Update specific fields on an item."""
    table = get_table()
    expr_parts = []
    attr_names = {}
    attr_values = {}

    for i, (key, val) in enumerate(updates.items()):
        placeholder = f"#f{i}"
        value_key = f":v{i}"
        expr_parts.append(f"{placeholder} = {value_key}")
        attr_names[placeholder] = key
        attr_values[value_key] = val

    resp = table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes", {})


def delete_item(pk: str, sk: str) -> None:
    table = get_table()
    table.delete_item(Key={"PK": pk, "SK": sk})


def query(pk: str, sk_prefix: str = None, index: str = None,
          limit: int = None, filter_expr=None) -> list[dict]:
    """Query by PK (and optional SK prefix) on main table or GSI."""
    table = get_table()

    if index == "GSI1":
        key_cond = Key("GSI1PK").eq(pk)
        if sk_prefix:
            key_cond = key_cond & Key("GSI1SK").begins_with(sk_prefix)
        kwargs = dict(IndexName="GSI1", KeyConditionExpression=key_cond)
    elif index == "GSI2":
        key_cond = Key("email").eq(pk)
        kwargs = dict(IndexName="GSI2", KeyConditionExpression=key_cond)
    else:
        key_cond = Key("PK").eq(pk)
        if sk_prefix:
            key_cond = key_cond & Key("SK").begins_with(sk_prefix)
        kwargs = dict(KeyConditionExpression=key_cond)

    if filter_expr:
        kwargs["FilterExpression"] = filter_expr
    if limit:
        kwargs["Limit"] = limit

    resp = table.query(**kwargs)
    return resp.get("Items", [])


def scan_prefix(pk_prefix: str, limit: int = 100) -> list[dict]:
    """Scan for items whose PK begins with a prefix (use sparingly)."""
    table = get_table()
    resp = table.scan(
        FilterExpression=Attr("PK").begins_with(pk_prefix),
        Limit=limit,
    )
    return resp.get("Items", [])


# ── Entity-specific helpers ──────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    items = query(pk=email.lower(), index="GSI2")
    return items[0] if items else None


def get_user(user_id: str) -> Optional[dict]:
    return get_item(f"USER#{user_id}", "PROFILE")


def get_appointment(appt_id: str) -> Optional[dict]:
    return get_item(f"APPT#{appt_id}", "DETAIL")


def get_appointments_by_status(status: str, date_from: str = None) -> list[dict]:
    sk_prefix = f"DATE#{date_from}" if date_from else "DATE#"
    return query(
        pk=f"STATUS#{status}",
        sk_prefix=sk_prefix,
        index="GSI1",
    )


def get_user_appointments(user_id: str) -> list[dict]:
    return query(pk=f"USER#{user_id}", sk_prefix="APPT#")


def get_site_config() -> Optional[dict]:
    return get_item("CONFIG#SITE", "SETTINGS")


def get_services(active_only: bool = True) -> list[dict]:
    items = query(pk_prefix="SERVICE#") if not active_only else []
    if active_only:
        items = scan_prefix("SERVICE#")
        items = [i for i in items if i.get("active", True)]
    return items


def get_available_slots(date: str) -> list[dict]:
    return query(pk=f"SLOT#{date}", sk_prefix="TIME#")
