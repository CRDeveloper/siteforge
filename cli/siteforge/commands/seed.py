"""
siteforge seed — populate DynamoDB with default data (admin user, services, availability).
"""
import json
import uuid
import secrets
import hashlib
import bcrypt
import os
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
SITES_DIR = Path(__file__).parent.parent.parent.parent / "sites"


def seed(
    id: str = typer.Option(..., "--id", help="Site identifier"),
    region: str = typer.Option("us-east-1", "--region", help="AWS region"),
    admin_email: str = typer.Option("", "--admin-email", help="Admin email (if different from config)"),
    admin_password: str = typer.Option("", "--admin-password", help="Admin password (generated if empty)"),
):
    """Seed a site with default data: admin user, services, and 30-day availability."""
    
    site_id = id.lower().replace(" ", "-")
    site_dir = SITES_DIR / site_id
    config_path = site_dir / "site-config.json"
    
    if not config_path.exists():
        console.print(f"[red]✗[/red] Site config not found: {config_path}")
        raise typer.Exit(1)
    
    # Load site config
    with open(config_path) as f:
        config = json.load(f)
    
    # Determine admin email and password
    admin_email = admin_email or config.get("email", {}).get("adminEmail", "")
    if not admin_email:
        console.print("[red]✗[/red] Admin email not specified and not in config")
        raise typer.Exit(1)
    
    if not admin_password:
        admin_password = secrets.token_urlsafe(12)
        console.print(f"[yellow]Generated admin password:[/yellow] {admin_password}")
    
    console.print(f"\n[bold]SiteForge — Seeding site:[/bold] [cyan]{site_id}[/cyan]")
    console.print(f"  Admin:  {admin_email}")
    console.print(f"  Region: {region}\n")
    
    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        # Table name matches CDK: sf-{site_id}-main
        table = dynamodb.Table(f"sf-{site_id}-main")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 1. Create admin user
            progress.add_task("[cyan]Creating admin user...", total=None)
            _create_admin_user(table, admin_email, admin_password)
            
            # 2. Seed services from config
            progress.add_task("[cyan]Seeding services...", total=None)
            service_count = _seed_services(table, config.get("services", []))
            
            # 3. Add 30-day availability slots
            progress.add_task("[cyan]Adding availability slots (30 days)...", total=None)
            slot_count = _seed_availability(table, config)
    
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"""[bold]Site seeded: {site_id}[/bold]

[yellow]Summary:[/yellow]
  • Admin user created (email: {admin_email})
  • {service_count} services added
  • {slot_count} availability slots for next 30 days

[yellow]Admin login:[/yellow]
  Email: {admin_email}
  Password: {admin_password}
  URL: https://{config.get('domain')}/admin

[dim]Save credentials securely — you'll need them to access the admin dashboard.[/dim]
""",
        title="[green]✓ Seed Complete[/green]",
        border_style="green",
    ))


def _create_admin_user(table, email: str, password: str):
    """Create admin user in DynamoDB."""
    user_id = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = datetime.utcnow().isoformat() + "Z"
    
    user = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "userId": user_id,
        "email": email,
        "firstName": "Admin",
        "lastName": "User",
        "phone": "",
        "passwordHash": pw_hash,
        "verified": True,  # Admin pre-verified
        "role": "admin",
        "createdAt": now,
        "updatedAt": now,
    }
    
    table.put_item(Item=user)
    console.print(f"[green]✓[/green] Admin user created: {email}")


def _seed_services(table, services: list) -> int:
    """Seed services from site config into DynamoDB."""
    if not services:
        console.print("[yellow]![/yellow] No services in config — skipping")
        return 0
    
    now = datetime.utcnow().isoformat() + "Z"
    count = 0
    
    for svc in services:
        service_id = svc.get("id") or str(uuid.uuid4())
        item = {
            "PK": f"SERVICE#{service_id}",
            "SK": "DETAIL",
            "serviceId": service_id,
            "name": svc.get("name", {}),
            "description": svc.get("description", {}),
            "durationMinutes": svc.get("durationMinutes", 50),
            "active": svc.get("active", True),
            "icon": svc.get("icon", ""),
            "createdAt": now,
            "updatedAt": now,
        }
        table.put_item(Item=item)
        count += 1
    
    console.print(f"[green]✓[/green] Added {count} service(s)")
    return count


def _seed_availability(table, config: dict) -> int:
    """Add availability slots for next 30 days, working days only (Mon-Fri), 9am-5pm."""
    now = datetime.utcnow()
    slots_per_day = 8  # 9am, 10am, 11am, 1pm, 2pm, 3pm, 4pm, 5pm (with 1h lunch break)
    times = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    count = 0
    
    for days_ahead in range(30):
        date_obj = now + timedelta(days=days_ahead)
        
        # Skip weekends (Monday=0, Sunday=6)
        if date_obj.weekday() >= 5:
            continue
        
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # Add time slots for this date
        for time_str in times:
            slot = {
                "PK": f"SLOT#{date_str}",
                "SK": f"TIME#{time_str}",
                "date": date_str,
                "time": time_str,
                "label": time_str,
            }
            table.put_item(Item=slot)
            count += 1
    
    console.print(f"[green]✓[/green] Added {count} availability slot(s)")
    return count

