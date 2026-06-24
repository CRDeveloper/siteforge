"""CORS preflight response helper."""
import os

DOMAIN = os.environ.get("DOMAIN", "*")


def cors_response() -> dict:
    return {
        "statusCode": 204,
        "headers": {
            "Access-Control-Allow-Origin": f"https://{DOMAIN}",
            "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Authorization,Content-Type",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        },
        "body": "",
    }
