"""siteforge dashboard — generate a static HTML status dashboard for all configured sites."""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import typer
import requests
from rich.console import Console

console = Console()
SITES_DIR = Path(__file__).parent.parent.parent.parent / "sites"
DEFAULT_OUTPUT = Path(__file__).parent.parent.parent.parent / "apps" / "admin" / "siteforge-dashboard.html"


def dashboard(
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for HTML dashboard (default: apps/admin/siteforge-dashboard.html)"
    ),
    ping: bool = typer.Option(
        False,
        "--ping",
        help="Check site endpoints with GET /api/config (3s timeout per site)"
    ),
):
    """Generate a static HTML dashboard of all configured SiteForge sites.
    
    Shows site name, domain, admin URL, language info, active modules, and last updated timestamp.
    Optional --ping flag adds live status checks for each site's /api/config endpoint.
    """
    output_path = Path(output) if output else DEFAULT_OUTPUT
    
    # Collect all site configs
    configs = list(SITES_DIR.glob("*/site-config.json"))
    
    if not configs:
        console.print("[yellow]No sites configured yet.[/yellow]")
        return
    
    sites_data = []
    
    for config_path in sorted(configs):
        try:
            with open(config_path) as f:
                config = json.load(f)
            
            # Get last modified time
            mtime = os.path.getmtime(config_path)
            last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            site_data = {
                "siteId": config.get("siteId", ""),
                "siteName": config.get("siteName", ""),
                "domain": config.get("domain", ""),
                "defaultLang": config.get("defaultLang", "en"),
                "supportedLangs": config.get("supportedLangs", []),
                "modules": config.get("modules", []),
                "lastUpdated": last_updated,
                "status": "unknown",
            }
            
            # Optional: ping the site
            if ping:
                site_data["status"] = _ping_site(config.get("domain", ""))
            
            sites_data.append(site_data)
        
        except Exception as e:
            console.print(f"[red]Error reading {config_path}: {e}[/red]")
    
    # Generate HTML
    html_content = _generate_html(sites_data)
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html_content)
    
    console.print(f"[green]✓ Dashboard generated:[/green] {output_path}")
    console.print(f"[cyan]{len(sites_data)} sites[/cyan]")
    if ping:
        console.print("[cyan]Live status checks enabled[/cyan]")


def _ping_site(domain: str) -> str:
    """Check if site's /api/config endpoint responds. Returns 'online' or 'offline'."""
    if not domain:
        return "offline"
    
    try:
        url = f"https://{domain}/api/config"
        response = requests.get(url, timeout=3)
        return "online" if response.status_code == 200 else "offline"
    except Exception:
        return "offline"


def _generate_html(sites_data: list) -> str:
    """Generate the complete standalone HTML dashboard."""
    
    # Build site cards
    site_cards_html = ""
    for site in sites_data:
        status_class = "status-online" if site["status"] == "online" else "status-offline" if site["status"] == "offline" else "status-unknown"
        status_dot = "🟢" if site["status"] == "online" else "🔴" if site["status"] == "offline" else "⚪"
        
        admin_url = f"https://{site['domain']}/admin" if site['domain'] else "#"
        domain_link = f"https://{site['domain']}" if site['domain'] else "#"
        
        modules_html = "".join([
            f'<span class="module-badge">{m}</span>'
            for m in site['modules']
        ])
        
        langs_html = "".join([
            f'<span class="lang-badge">{lang}</span>'
            for lang in site['supportedLangs']
        ])
        
        site_cards_html += f"""
        <div class="site-card">
            <div class="site-header">
                <h3 class="site-name">{site['siteName']}</h3>
                <span class="status-dot {status_class}">{status_dot}</span>
            </div>
            
            <div class="site-details">
                <div class="detail-row">
                    <label>Domain:</label>
                    <a href="{domain_link}" target="_blank" class="link">{site['domain']}</a>
                </div>
                
                <div class="detail-row">
                    <label>Admin:</label>
                    <a href="{admin_url}" target="_blank" class="link">{site['domain']}/admin</a>
                </div>
                
                <div class="detail-row">
                    <label>Default Language:</label>
                    <span>{site['defaultLang'].upper()}</span>
                </div>
                
                <div class="detail-row">
                    <label>Supported Languages:</label>
                    <div class="badges-group">{langs_html}</div>
                </div>
                
                <div class="detail-row">
                    <label>Active Modules:</label>
                    <div class="badges-group">{modules_html}</div>
                </div>
                
                <div class="detail-row">
                    <label>Last Updated:</label>
                    <span class="timestamp">{site['lastUpdated']}</span>
                </div>
            </div>
        </div>
"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SiteForge Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            padding: 40px 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            margin-bottom: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #fff;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        
        .header p {{
            font-size: 1.1em;
            color: #b0b0b0;
        }}
        
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        
        .stat-box {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px 25px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-box .number {{
            font-size: 2em;
            font-weight: 700;
            color: #00d4ff;
        }}
        
        .stat-box .label {{
            font-size: 0.9em;
            color: #b0b0b0;
            margin-top: 5px;
        }}
        
        .sites-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 24px;
        }}
        
        .site-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
        }}
        
        .site-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-4px);
        }}
        
        .site-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .site-name {{
            font-size: 1.4em;
            font-weight: 700;
            color: #fff;
            margin: 0;
        }}
        
        .status-dot {{
            font-size: 1.2em;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
        }}
        
        .status-dot.status-online {{
            color: #00ff00;
        }}
        
        .status-dot.status-offline {{
            color: #ff0000;
        }}
        
        .status-dot.status-unknown {{
            color: #808080;
        }}
        
        .site-details {{
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        
        .detail-row {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }}
        
        .detail-row label {{
            font-weight: 600;
            color: #00d4ff;
            min-width: 150px;
            font-size: 0.95em;
        }}
        
        .detail-row span {{
            color: #e0e0e0;
            word-break: break-word;
        }}
        
        .detail-row .link {{
            color: #00d4ff;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s ease;
        }}
        
        .detail-row .link:hover {{
            color: #00ffff;
            text-decoration: underline;
        }}
        
        .detail-row .timestamp {{
            color: #a0a0a0;
            font-size: 0.9em;
            font-family: 'Monaco', 'Courier New', monospace;
        }}
        
        .badges-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .module-badge {{
            display: inline-block;
            background: rgba(0, 212, 255, 0.15);
            border: 1px solid rgba(0, 212, 255, 0.3);
            color: #00d4ff;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .lang-badge {{
            display: inline-block;
            background: rgba(0, 255, 136, 0.15);
            border: 1px solid rgba(0, 255, 136, 0.3);
            color: #00ff88;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .footer {{
            margin-top: 60px;
            text-align: center;
            color: #606060;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .sites-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .detail-row {{
                flex-direction: column;
                gap: 4px;
            }}
            
            .detail-row label {{
                min-width: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 SiteForge Dashboard</h1>
            <p>Multi-site appointment booking platform</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="number">{len([s for s in sites_data if s['status'] == 'online'])}</div>
                <div class="label">Sites Online</div>
            </div>
            <div class="stat-box">
                <div class="number">{len([s for s in sites_data if s['status'] == 'offline'])}</div>
                <div class="label">Sites Offline</div>
            </div>
            <div class="stat-box">
                <div class="number">{len(sites_data)}</div>
                <div class="label">Total Sites</div>
            </div>
        </div>
        
        <div class="sites-grid">
            {site_cards_html}
        </div>
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • SiteForge Platform</p>
        </div>
    </div>
</body>
</html>
"""
    return html
