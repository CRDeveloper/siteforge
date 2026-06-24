"""
siteforge create — provision a new client site on AWS.
"""
import json
import os
import secrets
import subprocess
from pathlib import Path

import boto3
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
SITES_DIR = Path(__file__).parent.parent.parent.parent / "sites"
INFRA_DIR = Path(__file__).parent.parent.parent.parent / "infra" / "cdk"


def create(
    id: str = typer.Option(..., "--id", help="Unique site identifier (slug, e.g. my-business)"),
    domain: str = typer.Option(..., "--domain", help="Primary domain (e.g. mybusiness.com)"),
    admin: str = typer.Option(..., "--admin", help="Admin email address"),
    name: str = typer.Option("", "--name", help="Business name (defaults to --id)"),
    lang: str = typer.Option("en", "--lang", help="Default language"),
    langs: str = typer.Option("en,es", "--langs", help="Supported languages (comma-separated)"),
    theme_color: str = typer.Option("#2563eb", "--color", help="Primary brand color (hex)"),
    theme_mode: str = typer.Option("light", "--mode", help="Theme mode: light or dark"),
    region: str = typer.Option("us-east-1", "--region", help="AWS region"),
    skip_deploy: bool = typer.Option(False, "--skip-deploy", help="Skip CDK deploy (config only)"),
):
    site_id = id.lower().replace(" ", "-")
    site_name = name or site_id.replace("-", " ").title()
    supported_langs = [l.strip() for l in langs.split(",")]

    console.print(f"\n[bold]SiteForge — Creating site:[/bold] [cyan]{site_id}[/cyan]")
    console.print(f"  Domain: {domain}")
    console.print(f"  Admin:  {admin}")
    console.print(f"  Region: {region}\n")

    site_dir = SITES_DIR / site_id
    site_dir.mkdir(parents=True, exist_ok=True)

    # ── Generate site-config.json ─────────────────────────────────────────────
    config = {
        "siteId": site_id,
        "domain": domain,
        "siteName": site_name,
        "tagline": {lang: f"Welcome to {site_name}" for lang in supported_langs},
        "defaultLang": lang,
        "supportedLangs": supported_langs,
        "theme": {
            "primaryColor": theme_color,
            "accentColor": "#c9a96e",
            "backgroundColor": "#faf7f4",
            "textColor": "#2c2c2c",
            "mode": theme_mode,
            "fontDisplay": "Cormorant Garamond",
            "fontBody": "DM Sans",
        },
        "email": {
            "provider": "brevo",
            "senderName": site_name,
            "senderEmail": f"hello@{domain}",
            "adminEmail": admin,
            "apiKeyParam": f"/siteforge/{site_id}/brevo_api_key",
            "contactListId": 1,
            "templates": {
                "verifyEmail": 0,
                "passwordReset": 0,
                "appointmentConfirmed": 0,
                "appointmentAdminAlert": 0,
                "appointmentReminder": 0,
                "appointmentDeclined": 0,
                "appointmentRescheduled": 0,
                "appointmentCancelled": 0,
            },
        },
        "whatsapp": {"enabled": False},
        "appointments": {
            "windowDays": 30,
            "cancellationHours": 24,
            "reminderHoursBefore": 24,
        },
        "content": {
            "hero": {
                lang: {
                    "title": f"Welcome to {site_name}",
                    "subtitle": "Book your appointment online.",
                    "cta": "Book Now",
                }
            },
        },
        "services": [],
        "modules": [
            "user-auth", "appointments", "admin-dashboard",
            "notifications", "file-uploads",
        ],
        "seo": {
            lang: {
                "title": f"{site_name} — Online Booking",
                "description": f"Book your appointment with {site_name} online.",
            }
        },
    }

    config_path = site_dir / "site-config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    console.print(f"[green]✓[/green] Created {config_path}")

    # ── Store JWT secret in SSM ───────────────────────────────────────────────
    jwt_secret = secrets.token_urlsafe(64)
    try:
        ssm = boto3.client("ssm", region_name=region)
        ssm.put_parameter(
            Name=f"/siteforge/{site_id}/jwt_secret",
            Value=jwt_secret,
            Type="SecureString",
            Overwrite=False,
        )
        console.print("[green]✓[/green] JWT secret stored in SSM")
    except Exception as e:
        console.print(f"[yellow]![/yellow] Could not store JWT secret in SSM: {e}")
        console.print(f"  Run manually: aws ssm put-parameter --name /siteforge/{site_id}/jwt_secret --value <secret> --type SecureString")

    # ── CDK Deploy ────────────────────────────────────────────────────────────
    if not skip_deploy:
        console.print(f"\n[bold]Deploying AWS infrastructure...[/bold]")
        stack_name = f"SiteStack-{site_id}"
        try:
            result = subprocess.run(
                ["python", "-m", "aws_cdk", "deploy", stack_name, "--require-approval", "never"],
                cwd=INFRA_DIR,
                capture_output=False,
                check=True,
            )
            console.print(f"[green]✓[/green] CDK stack deployed: {stack_name}")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗[/red] CDK deploy failed. Check output above.")
            raise typer.Exit(1)

    # ── Print next steps ──────────────────────────────────────────────────────
    console.print(Panel(
        f"""[bold]Site created: {site_id}[/bold]

[yellow]Next steps:[/yellow]

1. [bold]Add Brevo API key to SSM:[/bold]
   aws ssm put-parameter \\
     --name /siteforge/{site_id}/brevo_api_key \\
     --value <YOUR_BREVO_KEY> \\
     --type SecureString

2. [bold]Add Cloudflare DNS records[/bold] (shown in CDK outputs above):
   CNAME  {domain}      →  <cloudfront-id>.cloudfront.net  (DNS only)
   CNAME  www.{domain}  →  <cloudfront-id>.cloudfront.net  (DNS only)

3. [bold]Validate ACM certificate[/bold] in AWS Console → ACM → your cert
   Add the CNAME validation records to Cloudflare DNS (DNS only)

4. [bold]Set up Brevo[/bold] — see 02-brevo-setup-guide.md

5. [bold]Deploy frontend:[/bold]
   siteforge deploy --id {site_id}

6. [bold]Seed DynamoDB[/bold] with default services:
   siteforge seed --id {site_id}

[dim]Admin dashboard: https://{domain}/admin[/dim]
""",
        title="[green]✓ Site Provisioned[/green]",
        border_style="green",
    ))
