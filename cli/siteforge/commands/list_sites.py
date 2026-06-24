"""siteforge list — list all configured sites."""
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

console = Console()
SITES_DIR = Path(__file__).parent.parent.parent.parent / "sites"


def list_sites():
    configs = list(SITES_DIR.glob("*/site-config.json"))
    if not configs:
        console.print("[yellow]No sites configured yet.[/yellow]")
        console.print("Run: siteforge create --id mysite --domain mysite.com --admin admin@mysite.com")
        return

    table = Table(title="SiteForge — Configured Sites", show_header=True, header_style="bold")
    table.add_column("Site ID", style="cyan")
    table.add_column("Domain")
    table.add_column("Name")
    table.add_column("Lang")
    table.add_column("Modules")

    for p in sorted(configs):
        with open(p) as f:
            c = json.load(f)
        table.add_row(
            c.get("siteId", ""),
            c.get("domain", ""),
            c.get("siteName", ""),
            c.get("defaultLang", ""),
            ", ".join(c.get("modules", [])),
        )

    console.print(table)
