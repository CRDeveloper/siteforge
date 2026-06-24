#!/usr/bin/env python3
"""
SiteForge CDK v2 Infrastructure
Usage:
  cdk deploy SharedStack
  cdk deploy SiteStack-serenity-therapy
  cdk deploy --all
"""
import aws_cdk as cdk
import json
import os
import sys
from pathlib import Path

from stacks.shared_stack import SharedStack
from stacks.site_stack import SiteStack

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

    SiteStack(
        app,
        f"SiteStack-{site_id}",
        site_config=config,
        shared_stack=shared,
        env=cdk.Environment(
            account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
            region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
        ),
        description=f"SiteForge site: {config['siteName']} ({site_id})",
    )

app.synth()
