"""siteforge config — read or update a site-config.json field."""
import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

console = Console()
SITES_DIR = Path(__file__).parent.parent.parent.parent / "sites"


def config_cmd(
    id: str = typer.Option(..., "--id"),
    get: Optional[str] = typer.Option(None, "--get", help="Dot-path to read, e.g. theme.primaryColor"),
    set_: Optional[str] = typer.Option(None, "--set", help="Dot-path=value to write, e.g. theme.primaryColor=#ff0000"),
):
    config_path = SITES_DIR / id / "site-config.json"
    if not config_path.exists():
        console.print(f"[red]✗[/red] No config found for site: {id}")
        raise typer.Exit(1)

    with open(config_path) as f:
        config = json.load(f)

    if get:
        value = _get_nested(config, get)
        console.print(f"{get} = {json.dumps(value, indent=2)}")

    if set_:
        if "=" not in set_:
            console.print("[red]--set requires KEY=VALUE format[/red]")
            raise typer.Exit(1)
        key, _, raw_value = set_.partition("=")
        # Try to parse as JSON, fall back to string
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value

        _set_nested(config, key, value)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        console.print(f"[green]✓[/green] Set {key} = {json.dumps(value)}")
        console.print(f"  Run 'siteforge deploy --id {id}' to apply changes.")


def _get_nested(obj: dict, path: str):
    parts = path.split(".")
    for p in parts:
        if isinstance(obj, dict):
            obj = obj.get(p)
        else:
            return None
    return obj


def _set_nested(obj: dict, path: str, value):
    parts = path.split(".")
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value
