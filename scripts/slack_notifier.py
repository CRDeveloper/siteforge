#!/usr/bin/env python3

"""
Slack Notifier for SiteForge Deployments

Sends deployment notifications to Slack via Incoming Webhooks.
Fetches the webhook URL from AWS Secrets Manager at runtime.

Usage:
    from slack_notifier import SlackNotifier

    notifier = SlackNotifier(secret_name="siteforge/slack-webhook-url")
    notifier.send_message(text="Site deployment started 🚀", emoji="🚀")
    notifier.send_deployment_started(site_id="serenity-therapy")
    notifier.send_deployment_completed(site_id="serenity-therapy", duration="5 min")
    notifier.send_deployment_failed(site_id="serenity-therapy", step="Build Frontend", error="npm build failed")
"""

import json
import logging
import os
import sys
import urllib.request
import urllib.error
from typing import Optional
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    boto3 = None
    BotoCoreError = Exception
    ClientError = Exception

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Thin wrapper around Slack Incoming Webhooks.
    Fetches the webhook URL once from Secrets Manager and caches it.
    
    Gracefully handles missing AWS credentials (notifications are optional).
    """

    def __init__(
        self,
        secret_name: str = 'siteforge/slack-webhook-url',
        region_name: str = "us-east-1",
        enabled: bool = True,
    ):
        self._secret_name = secret_name
        self._region_name = region_name
        self._webhook_url: Optional[str] = None  # lazily fetched
        self._enabled = enabled
        self._fetch_failed = False

    # ------------------------------------------------------------------
    # Public API — Deployment Lifecycle Events
    # ------------------------------------------------------------------

    def send_message(self, text: str, emoji: str = "ℹ️") -> bool:
        """
        Send a plain-text message to the configured Slack channel.

        Args:
            text: The message string. Slack mrkdwn is supported.
            emoji: Optional emoji to prefix the message.

        Returns:
            True on success, False if disabled or on error.
        """
        if not self._enabled or self._fetch_failed:
            return False
        
        full_text = f"{emoji} {text}" if emoji else text
        payload = {"text": full_text}
        return self._post(payload)

    def send_deployment_started(self, site_id: str) -> bool:
        """Send deployment started notification."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"🚀 *SiteForge Deployment STARTED* for site `{site_id}` at {timestamp}"
        return self.send_message(text, emoji="")

    def send_deployment_completed(
        self,
        site_id: str,
        duration: str = "",
        domain: str = "",
    ) -> bool:
        """Send deployment completed notification."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration_str = f" ({duration})" if duration else ""
        domain_str = f"\n• Domain: `{domain}`" if domain else ""
        
        text = (
            f"✅ *SiteForge Deployment COMPLETED* for site `{site_id}`{duration_str}\n"
            f"Finished at {timestamp}{domain_str}"
        )
        return self.send_message(text, emoji="")

    def send_deployment_failed(
        self,
        site_id: str,
        step: str = "",
        error: str = "",
    ) -> bool:
        """Send deployment failed notification."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        step_str = f"\n• Step: {step}" if step else ""
        error_str = f"\n• Error: {error}" if error else ""
        
        text = (
            f"❌ *SiteForge Deployment FAILED* for site `{site_id}`\n"
            f"Failed at {timestamp}{step_str}{error_str}"
        )
        return self.send_message(text, emoji="")

    def send_site_created(self, site_id: str, domain: str, name: str) -> bool:
        """Send site created notification."""
        text = (
            f"✨ *New SiteForge Site Created*\n"
            f"• Site ID: `{site_id}`\n"
            f"• Name: {name}\n"
            f"• Domain: `{domain}`"
        )
        return self.send_message(text, emoji="")

    def send_site_destroyed(self, site_id: str) -> bool:
        """Send site destroyed notification."""
        text = (
            f"🗑️ *SiteForge Site DESTROYED*\n"
            f"• Site ID: `{site_id}`"
        )
        return self.send_message(text, emoji="")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_webhook_url(self) -> Optional[str]:
        """
        Fetch and cache the webhook URL from Secrets Manager.
        
        Returns None if AWS is not configured (graceful degradation).
        """
        if self._webhook_url:
            return self._webhook_url
        
        if not boto3:
            logger.warning("boto3 not installed, Slack notifications disabled")
            self._fetch_failed = True
            return None
        
        try:
            client = boto3.client("secretsmanager", region_name=self._region_name)
            response = client.get_secret_value(SecretId=self._secret_name)
            self._webhook_url = response["SecretString"].strip()
            return self._webhook_url
        except Exception as exc:
            logger.warning("Failed to fetch Slack webhook from Secrets Manager: %s", exc)
            logger.debug("Slack notifications disabled (AWS credentials may not be configured)")
            self._fetch_failed = True
            return None

    def _post(self, payload: dict) -> bool:
        """POST a JSON payload to the Slack webhook endpoint."""
        if not self._enabled or self._fetch_failed:
            return False
        
        try:
            url = self._get_webhook_url()
            if not url:
                return False
            
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8")
                if resp.status == 200 and body == "ok":
                    logger.debug("Slack notification sent successfully")
                    return True
                logger.warning("Unexpected Slack response [%s]: %s", resp.status, body)
                return False
        except urllib.error.HTTPError as exc:
            logger.warning("Slack webhook HTTP error %s", exc.code)
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("Slack notification failed: %s", exc)
            return False


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    # Test notifications
    logging.basicConfig(level=logging.INFO)
    
    # Check if Slack is enabled
    slack_enabled = os.environ.get("SLACK_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    
    notifier = SlackNotifier(enabled=slack_enabled)
    
    print(f"Slack notifications enabled: {slack_enabled}")
    print("")
    
    if slack_enabled:
        print("Sending test notifications...")
        notifier.send_deployment_started("test-site")
        notifier.send_message("This is a test message", emoji="🧪")
        notifier.send_deployment_completed("test-site", duration="2 min", domain="test-site.com")
    else:
        print("Slack notifications disabled. Set SLACK_NOTIFICATIONS_ENABLED=true to enable.")
        print("")
        print("Setup Slack:")
        print("  1. Create Slack app at https://api.slack.com/apps")
        print("  2. Enable Incoming Webhooks")
        print("  3. Add New Webhook to Workspace")
        print("  4. Copy webhook URL")
        print("  5. Store in AWS Secrets Manager:")
        print("     aws secretsmanager create-secret \\")
        print("       --name siteforge/slack-webhook-url \\")
        print("       --secret-string 'https://hooks.slack.com/...'")
        print("  6. Set SLACK_NOTIFICATIONS_ENABLED=true in .env")
