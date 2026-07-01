#!/usr/bin/env python3
"""
SiteForge CDK v2 Infrastructure
Usage:
  cdk deploy SharedStack
  cdk deploy SfSiteStack-serenity-therapy
  cdk deploy --all
"""
import aws_cdk as cdk
import json
import os
import sys
from pathlib import Path

from stacks.shared_stack import SharedStack
from stacks.site_stack import SiteStack
from stacks.monitoring_stack import MonitoringStack

app = cdk.App()

# ── Shared stack (deploy once per AWS account) ──────────────────────────────
shared = SharedStack(
    app,
    "SiteForgeShared",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
    description="SiteForge shared infrastructure (SSM, SES domain identity)",
)

# ── Site stacks (one per client site) ───────────────────────────────────────
sites_dir = Path(__file__).parent.parent.parent / "sites"

for site_config_path in sites_dir.glob("*/site-config.json"):
    with open(site_config_path) as f:
        config = json.load(f)

    site_id = config["siteId"]

    site_stack = SiteStack(
        app,
        f"SfSiteStack-{site_id}",
        site_config=config,
        shared_stack=shared,
        env=cdk.Environment(
            account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
            region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
        ),
        description=f"SiteForge site: {config['siteName']} ({site_id})",
    )

    # Monitoring stack for this site
    MonitoringStack(
        app,
        f"SfMonitoring-{site_id}",
        site_id=site_id,
        site_name=config["siteName"],
        lambda_fn=site_stack.lambda_fn,
        http_api=site_stack.http_api,
        table=site_stack.table,
        admin_email=config["email"]["adminEmail"],
        env=cdk.Environment(
            account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
            region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
        ),
        description=f"SiteForge monitoring: {config['siteName']} ({site_id})",
    )

app.synth()
