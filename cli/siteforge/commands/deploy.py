"""
siteforge deploy — build Next.js and upload to S3 + CloudFront invalidation.
"""
import json
import os
import subprocess
from pathlib import Path

import boto3
import typer
from rich.console import Console

console = Console()

REPO_ROOT = Path(__file__).parent.parent.parent.parent
FRONTEND_DIR = REPO_ROOT / "apps" / "frontend"
SITES_DIR = REPO_ROOT / "sites"


def deploy(
    id: str = typer.Option(..., "--id", help="Site ID to deploy"),
    region: str = typer.Option("us-east-1", "--region"),
    skip_build: bool = typer.Option(False, "--skip-build", help="Skip Next.js build"),
    skip_invalidation: bool = typer.Option(False, "--skip-invalidation"),
):
    site_id = id
    config_path = SITES_DIR / site_id / "site-config.json"

    if not config_path.exists():
        console.print(f"[red]✗[/red] No site config found at {config_path}")
        raise typer.Exit(1)

    with open(config_path) as f:
        config = json.load(f)

    domain = config["domain"]
    bucket_name = f"siteforge-{site_id}-frontend"

    console.print(f"\n[bold]Deploying:[/bold] [cyan]{site_id}[/cyan] → s3://{bucket_name}")

    # ── 1. Build Next.js ──────────────────────────────────────────────────────
    if not skip_build:
        console.print("\n[bold]Building Next.js...[/bold]")
        env = {
            **os.environ,
            "SITE_ID": site_id,
            "NEXT_PUBLIC_SITE_ID": site_id,
            "NEXT_PUBLIC_SITE_NAME": config["siteName"],
            "NEXT_PUBLIC_DEFAULT_LANG": config["defaultLang"],
            "NEXT_PUBLIC_SUPPORTED_LANGS": json.dumps(config["supportedLangs"]),
            "NEXT_PUBLIC_THEME": json.dumps(config["theme"]),
            "NEXT_PUBLIC_API_URL": f"https://{domain}/api",
            "NODE_ENV": "production",
        }
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=FRONTEND_DIR,
            env=env,
            check=True,
        )
        console.print("[green]✓[/green] Next.js build complete")

    # ── 2. Sync to S3 ─────────────────────────────────────────────────────────
    console.print(f"\n[bold]Uploading to S3...[/bold]")
    out_dir = FRONTEND_DIR / "out"
    if not out_dir.exists():
        console.print(f"[red]✗[/red] Build output not found at {out_dir}. Run build first.")
        raise typer.Exit(1)

    result = subprocess.run(
        [
            "aws", "s3", "sync", str(out_dir), f"s3://{bucket_name}",
            "--delete",
            "--cache-control", "public,max-age=31536000,immutable",
            "--exclude", "*.html",
            "--region", region,
        ],
        check=True,
    )
    # Upload HTML separately with no-cache
    subprocess.run(
        [
            "aws", "s3", "sync", str(out_dir), f"s3://{bucket_name}",
            "--cache-control", "no-cache,no-store,must-revalidate",
            "--include", "*.html",
            "--region", region,
        ],
        check=True,
    )
    console.print("[green]✓[/green] Files uploaded to S3")

    # ── 3. CloudFront invalidation ────────────────────────────────────────────
    if not skip_invalidation:
        console.print("\n[bold]Invalidating CloudFront cache...[/bold]")
        try:
            cf = boto3.client("cloudfront", region_name=region)
            # Find distribution by domain
            dists = cf.list_distributions()["DistributionList"]["Items"]
            dist_id = None
            for d in dists:
                aliases = d.get("Aliases", {}).get("Items", [])
                if domain in aliases or f"www.{domain}" in aliases:
                    dist_id = d["Id"]
                    break

            if dist_id:
                cf.create_invalidation(
                    DistributionId=dist_id,
                    InvalidationBatch={
                        "Paths": {"Quantity": 1, "Items": ["/*"]},
                        "CallerReference": f"siteforge-deploy-{site_id}",
                    },
                )
                console.print(f"[green]✓[/green] CloudFront invalidation created for {dist_id}")
            else:
                console.print(f"[yellow]![/yellow] Could not find CloudFront distribution for {domain}")
        except Exception as e:
            console.print(f"[yellow]![/yellow] CloudFront invalidation failed: {e}")

    console.print(f"\n[green]✓ Deployment complete → https://{domain}[/green]\n")
