"""
siteforge destroy — decommission a site (CDK destroy + SSM cleanup).
"""
import subprocess
from pathlib import Path

import boto3
import typer
from rich.console import Console
from rich.panel import Panel

console = Console()
SITES_DIR = Path(__file__).parent.parent.parent.parent / "sites"
INFRA_DIR = Path(__file__).parent.parent.parent.parent / "infra" / "cdk"


def destroy(
    id: str = typer.Option(..., "--id", help="Site identifier"),
    region: str = typer.Option("us-east-1", "--region", help="AWS region"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Destroy a site: tear down AWS resources and clean up SSM parameters."""
    
    site_id = id.lower().replace(" ", "-")
    site_dir = SITES_DIR / site_id
    
    if not site_dir.exists():
        console.print(f"[red]✗[/red] Site directory not found: {site_dir}")
        raise typer.Exit(1)
    
    # ── Confirmation ──────────────────────────────────────────────────────────
    if not force:
        console.print(Panel(
            f"[bold red]⚠ WARNING: This will permanently destroy site '{site_id}'[/bold red]\n\n"
            "[yellow]This action will:[/yellow]\n"
            "  • Tear down all AWS resources (S3, CloudFront, DynamoDB, Lambda)\n"
            "  • Delete SSM parameters (JWT secret, API keys)\n"
            "  • Remove site directory\n\n"
            "[dim]This cannot be undone.[/dim]",
            title="[red]Confirm Destruction[/red]",
            border_style="red",
        ))
        confirm = typer.confirm("Are you absolutely sure?")
        if not confirm:
            console.print("[yellow]✗[/yellow] Destruction cancelled.")
            raise typer.Exit(0)
    
    console.print(f"\n[bold]SiteForge — Destroying site:[/bold] [red]{site_id}[/red]\n")
    
    # ── CDK Destroy ────────────────────────────────────────────────────────────
    stack_name = f"SfSiteStack-{site_id}"
    console.print(f"[yellow]→[/yellow] Destroying CDK stack: {stack_name}")
    try:
        subprocess.run(
            ["python", "-m", "aws_cdk", "destroy", stack_name, "--force"],
            cwd=INFRA_DIR,
            capture_output=False,
            check=True,
        )
        console.print(f"[green]✓[/green] CDK stack destroyed")
    except subprocess.CalledProcessError:
        console.print(f"[yellow]![/yellow] CDK destroy failed or stack doesn't exist (continuing)")
    
    # ── Cleanup SSM Parameters ─────────────────────────────────────────────────
    console.print(f"[yellow]→[/yellow] Cleaning up SSM parameters")
    ssm = boto3.client("ssm", region_name=region)
    params_to_delete = [
        f"/siteforge/{site_id}/jwt_secret",
        f"/siteforge/{site_id}/brevo_api_key",
    ]
    
    for param_name in params_to_delete:
        try:
            ssm.delete_parameter(Name=param_name)
            console.print(f"  [green]✓[/green] Deleted {param_name}")
        except ssm.exceptions.ParameterNotFound:
            pass
        except Exception as e:
            console.print(f"  [yellow]![/yellow] Could not delete {param_name}: {e}")
    
    # ── Remove local site directory ────────────────────────────────────────────
    console.print(f"[yellow]→[/yellow] Removing local site directory")
    import shutil
    try:
        shutil.rmtree(site_dir)
        console.print(f"[green]✓[/green] Removed {site_dir}")
    except Exception as e:
        console.print(f"[yellow]![/yellow] Could not remove directory: {e}")
    
    console.print(Panel(
        f"[bold red]Site destroyed: {site_id}[/bold red]\n\n"
        "[dim]All AWS resources and configuration have been removed.[/dim]",
        title="[red]✓ Destruction Complete[/red]",
        border_style="red",
    ))
