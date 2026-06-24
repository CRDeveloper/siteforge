#!/usr/bin/env python3
"""
siteforge — CLI installer for the SiteForge platform.

Usage:
  siteforge create   --id mybusiness --domain mybusiness.com --admin admin@mybusiness.com
  siteforge deploy   --id mybusiness
  siteforge config   --id mybusiness --set theme.primaryColor=#ff6b35
  siteforge list
  siteforge destroy  --id mybusiness
  siteforge seed     --id mybusiness
  siteforge add-module --id mybusiness --module payments
"""

import typer
from typing import Optional
from .commands.create import create
from .commands.deploy import deploy
from .commands.config import config_cmd
from .commands.list_sites import list_sites
from .commands.destroy import destroy
from .commands.seed import seed
from .commands.add_module import add_module

app = typer.Typer(
    name="siteforge",
    help="SiteForge platform CLI — create and manage client websites",
    add_completion=False,
)

app.command("create")(create)
app.command("deploy")(deploy)
app.command("config")(config_cmd)
app.command("list")(list_sites)
app.command("destroy")(destroy)
app.command("seed")(seed)
app.command("add-module")(add_module)

if __name__ == "__main__":
    app()
