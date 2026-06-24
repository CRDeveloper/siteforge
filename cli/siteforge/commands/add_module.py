"""
siteforge add-module — add a module to a site and deploy Lambda changes.
"""
import json
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()
SITES_DIR = Path(__file__).parent.parent.parent.parent / "sites"
INFRA_DIR = Path(__file__).parent.parent.parent.parent / "infra" / "cdk"

AVAILABLE_MODULES = {
    "payments": "Stripe payment processing for bookings",
    "whatsapp": "WhatsApp notifications via Brevo",
    "blog": "Markdown-based blog with S3 storage",
    "gallery": "Photo gallery with S3 backend",
    "analytics": "Plausible or CloudWatch analytics dashboard",
    "sms": "SMS notifications (Twilio or Brevo)",
}


def add_module(
    id: str = typer.Option(..., "--id", help="Site identifier"),
    module: str = typer.Option(..., "--module", help="Module to add"),
    region: str = typer.Option("us-east-1", "--region", help="AWS region"),
):
    """Add a module to a site and deploy Lambda updates."""
    
    site_id = id.lower().replace(" ", "-")
    site_dir = SITES_DIR / site_id
    config_path = site_dir / "site-config.json"
    
    if not config_path.exists():
        console.print(f"[red]✗[/red] Site config not found: {config_path}")
        raise typer.Exit(1)
    
    if module not in AVAILABLE_MODULES:
        console.print(f"[red]✗[/red] Unknown module: {module}")
        console.print(f"\n[yellow]Available modules:[/yellow]")
        for mod_name, mod_desc in AVAILABLE_MODULES.items():
            console.print(f"  • {mod_name}: {mod_desc}")
        raise typer.Exit(1)
    
    with open(config_path) as f:
        config = json.load(f)
    
    modules = config.get("modules", [])
    if module in modules:
        console.print(f"[yellow]![/yellow] Module '{module}' already enabled for {site_id}")
        raise typer.Exit(0)
    
    console.print(f"\n[bold]SiteForge — Adding module:[/bold] [cyan]{module}[/cyan]")
    console.print(f"  Site:   {site_id}")
    console.print(f"  Module: {AVAILABLE_MODULES[module]}\n")
    
    # Update config
    console.print("[yellow]→[/yellow] Updating site-config.json")
    modules.append(module)
    config["modules"] = sorted(modules)
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    console.print(f"[green]✓[/green] Added '{module}' to modules list")
    
    # Module-specific config
    if module == "payments":
        if "stripe" not in config:
            config["stripe"] = {
                "publishableKey": "",
                "webhookSecret": "",
                "enabled": False,
            }
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            console.print("[green]✓[/green] Added Stripe config (requires webhook secret)")
    
    elif module == "whatsapp":
        config["whatsapp"]["enabled"] = True
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        console.print("[green]✓[/green] Enabled WhatsApp module")
    
    elif module == "analytics":
        if "analytics" not in config:
            config["analytics"] = {
                "provider": "plausible",
                "siteId": "",
            }
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            console.print("[green]✓[/green] Added analytics config")
    
    # Deploy CDK stack
    console.print("[yellow]→[/yellow] Deploying CDK stack with new module")
    stack_name = f"SfSiteStack-{site_id}"
    try:
        subprocess.run(
            ["python", "-m", "aws_cdk", "deploy", stack_name, "--require-approval", "never"],
            cwd=INFRA_DIR,
            capture_output=False,
            check=True,
        )
        console.print("[green]✓[/green] CDK stack updated")
    except subprocess.CalledProcessError:
        console.print("[red]✗[/red] CDK deploy failed. Review output above.")
        raise typer.Exit(1)
    
    # Summary
    module_list = "\n".join(f"  • {m}" for m in config["modules"])
    console.print(Panel(
        f"[bold green]Module added: {module}[/bold green]\n\n"
        f"[yellow]Current modules:[/yellow]\n"
        f"{module_list}\n\n"
        f"[dim]Lambda functions have been updated. Changes take effect immediately.[/dim]",
        title="[green]✓ Module Added[/green]",
        border_style="green",
    ))
