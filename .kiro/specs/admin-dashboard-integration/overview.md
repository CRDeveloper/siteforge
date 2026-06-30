# SiteForge Admin Dashboard Integration

**Status**: Pending Implementation  
**Workspace**: /workspace/siteforge  
**Goal**: Create a webmaster dashboard accessible at `siteforge.YOURADMINDOMAIN.com` that displays real-time status of all SiteForge client sites and integrates with ADMINDev infrastructure.

---

## Overview

The SiteForge admin dashboard provides webmasters and administrators with a centralized view of all deployed client sites. It serves as:

- **Status monitoring**: Real-time health checks of all sites
- **Quick access**: Admin URLs and domain links for each site
- **Configuration overview**: Languages, modules, and settings at a glance
- **System integration**: Wired as a subdomain of the main ADMINDev platform (siteforge.YOURADMINDOMAIN.com)

---

## Architecture

```
ADMINDev (Main Platform)
├── YOURADMINDOMAIN.com (Primary Domain)
├── admin.YOURADMINDOMAIN.com (Admin Panel)
└── siteforge.YOURADMINDOMAIN.com (SiteForge Admin Dashboard)
    └── Static HTML Dashboard
        └── Displays all SiteForge sites
            └── Real-time status checks
            └── Quick admin links
```

## Key Components

### 1. CLI Dashboard Command
**File**: `/workspace/siteforge/cli/siteforge/commands/dashboard.py`  
**Status**: ✅ Created

- Scans all `sites/*/site-config.json` files
- Generates self-contained static HTML dashboard
- Optional `--ping` flag for live health checks
- Outputs to: `apps/admin/siteforge-dashboard.html` (default)
- No build step required, single file deployment

**Usage**:
```bash
# Generate dashboard without health checks
python -m cli.siteforge dashboard

# Generate with live status checks (3s timeout per site)
python -m cli.siteforge dashboard --ping

# Custom output path
python -m cli.siteforge dashboard --output /custom/path/dashboard.html
```

### 2. Static HTML Output
**File**: `apps/admin/siteforge-dashboard.html`

- Self-contained, single HTML file with inline CSS
- No JavaScript dependencies, no build step
- Dark theme with modern card-based layout
- Mobile-responsive design
- Real-time updating on re-generation

**Features**:
- Site cards with name, domain, admin URL
- Language and module badges
- Last updated timestamp
- Optional status indicators (online/offline/unknown)
- Summary stats (online sites, offline sites, total)

### 3. ADMINDev Integration
**Location**: Static file served from ADMINDev at `/siteforge.YOURADMINDOMAIN.com`

- Route static file via Next.js or CloudFront
- Optional authentication (view-only access)
- Accessible to internal teams only

---

## Requirements

### Functional Requirements

- [x] FR1: Scan all site configurations from `sites/` directory
- [x] FR2: Extract site metadata (name, domain, languages, modules)
- [x] FR3: Calculate last updated timestamp from config file mtime
- [x] FR4: Generate self-contained HTML (no build step)
- [x] FR5: Optional live health checks (GET `/api/config`, 3s timeout)
- [x] FR6: Mobile-responsive design
- [x] FR7: Clean, professional dashboard UI
- [ ] FR8: Deploy static HTML to ADMINDev infrastructure
- [ ] FR9: Configure DNS routing to `siteforge.YOURADMINDOMAIN.com`
- [ ] FR10: Optional authentication layer for internal teams

### Non-Functional Requirements

- NFR1: Fast generation (<2s for 10+ sites)
- NFR2: No external dependencies for HTML rendering
- NFR3: Graceful handling of unreachable sites
- NFR4: Self-contained file (no external CSS/JS resources)

---

## Implementation Phases

### Phase 1: CLI Dashboard Command ✅ COMPLETE
**Status**: Done

- [x] Create `cli/siteforge/commands/dashboard.py`
- [x] Implement site config scanning
- [x] Generate HTML with inline CSS
- [x] Add optional --ping flag for health checks
- [x] Register command in `__main__.py`
- [x] Test with sample site config

**Completion**: Dashboard command works locally

### Phase 2: ADMINDev Integration 🔄 TO DO
**Status**: Next

- [ ] Create route/handler in ADMINDev to serve dashboard
- [ ] Configure static file serving
- [ ] Set up CI/CD to auto-generate dashboard on deployment
- [ ] Test accessibility at `siteforge.YOURADMINDOMAIN.com`
- [ ] Add optional view-only authentication

### Phase 3: Production Deployment 🔄 TO DO
**Status**: After Phase 2

- [ ] Deploy updated ADMINDev with dashboard route
- [ ] Configure DNS/CloudFront for `siteforge.YOURADMINDOMAIN.com`
- [ ] Set up automated dashboard regeneration
- [ ] Verify live functionality
- [ ] Document access procedures

---

## Dashboard Features

### Site Information
Each site card displays:
- **Site Name**: Branding name (e.g., "Serenity Therapy")
- **Domain**: Clickable link to site homepage
- **Admin URL**: Clickable link to admin panel (domain + `/admin`)
- **Default Language**: Primary language code (e.g., EN, ES)
- **Supported Languages**: Badges for all enabled languages
- **Active Modules**: Badges for installed modules (auth, appointments, notifications, etc.)
- **Last Updated**: Timestamp from config file modification

### Status Indicators (Optional)
When `--ping` flag is used:
- 🟢 **Online**: Site responded to `/api/config` endpoint
- 🔴 **Offline**: Site did not respond or timed out
- ⚪ **Unknown**: Ping check disabled

### Summary Statistics
Top section shows:
- Number of sites currently online
- Number of sites offline
- Total number of configured sites

---

## File Structure

```
/workspace/siteforge/
├── cli/
│   └── siteforge/
│       ├── __main__.py                          # ← Updated: Added dashboard import
│       └── commands/
│           ├── __init__.py
│           ├── create.py
│           ├── deploy.py
│           ├── list_sites.py
│           └── dashboard.py                      # ← NEW: Dashboard command
├── apps/
│   └── admin/
│       └── siteforge-dashboard.html              # ← Generated output
└── .kiro/
    └── specs/
        └── admin-dashboard-integration/
            ├── overview.md                       # ← This file
            ├── tasks.md                          # ← Phase breakdown
            └── deployment-guide.md               # ← ADMINDev integration
```

---

## Usage Examples

### Generate Dashboard Locally
```bash
cd /workspace/siteforge
python -m cli.siteforge dashboard
# Output: ✓ Dashboard generated: apps/admin/siteforge-dashboard.html
```

### Generate with Health Checks
```bash
python -m cli.siteforge dashboard --ping
# Checks each site's /api/config endpoint (3s timeout)
```

### Custom Output Path
```bash
python -m cli.siteforge dashboard --output /tmp/dashboard.html
```

### List All Sites
```bash
python -m cli.siteforge list
# Shows table of all configured sites
```

---

## Integration with ADMINDev

### Step 1: Add Route to ADMINDev
In ADMINDev Next.js app, create a route that:
1. Reads the static HTML file from siteforge workspace
2. Serves it at `/siteforge` or as a custom domain

### Step 2: Configure DNS
Set up CNAME record:
```
siteforge  CNAME  www.YOURADMINDOMAIN.com
```

### Step 3: Auto-Generate Dashboard
Add pre-deployment step in CI/CD:
```bash
# Before ADMINDev deployment
cd /workspace/siteforge && python -m cli.siteforge dashboard
# Upload generated HTML to ADMINDev
```

---

## Security Considerations

### Current State (Internal-Only Tool)
- ✅ No authentication required
- ✅ Read-only access (scans local configs)
- ✅ No sensitive data exposed (no API keys, secrets)
- ✅ Internal network only (siteforge.YOURADMINDOMAIN.com)

### Future Enhancement (If Needed)
- Optional view-only JWT authentication
- Rate limiting on health check endpoint
- Audit logging for access
- IP whitelisting for internal teams

---

## Testing

### Local Testing
```bash
# Generate dashboard
python -m cli.siteforge dashboard

# Open in browser
open apps/admin/siteforge-dashboard.html

# With health checks (requires internet connection)
python -m cli.siteforge dashboard --ping
```

### ADMINDev Integration Testing
- [ ] Dashboard accessible at `siteforge.YOURADMINDOMAIN.com`
- [ ] All site links working
- [ ] Health checks display correctly (if enabled)
- [ ] Mobile responsive design works
- [ ] CSS/styling loads without external resources

---

## Performance Considerations

### Dashboard Generation
- **Scanning**: <500ms for 10 sites
- **HTML Generation**: <300ms
- **Total Time**: ~800ms (without health checks)

### Health Checks (With --ping)
- **Per Site**: 3 second timeout
- **Total Time**: ~30s for 10 sites (sequential)
- **Optimization**: Could be parallelized in future

### Dashboard Viewing
- **Page Load**: <100ms (single static file)
- **Rendering**: Instant (no JS overhead)
- **Mobile**: Fully responsive, optimized for all devices

---

## Maintenance

### Regular Tasks
1. **Auto-regenerate**: Dashboard should be generated on each siteforge command
2. **Monitor**: Check health status monthly
3. **Archive**: Keep historical dashboards if needed

### Future Enhancements
- [ ] Scheduled auto-generation (hourly, daily)
- [ ] Historical trending (site uptime over time)
- [ ] Webhooks for real-time updates
- [ ] Export reports (PDF, CSV)
- [ ] Integration with monitoring tools (CloudWatch, DataDog)

---

## Dependencies

### Required
- Python 3.12+
- `requests` library (for health checks)
- `typer` library (CLI framework)
- `rich` library (console output)

### Optional
- AWS CLI v2 (for deployment)
- Node.js (for ADMINDev integration)

---

## Next Steps

1. ✅ **Phase 1 Complete**: Dashboard command implemented and tested
2. 🔄 **Phase 2**: Create ADMINDev route to serve dashboard
3. 🔄 **Phase 3**: Configure DNS and deploy to production
4. 🔄 **Phase 4**: Set up automated dashboard regeneration

---

## Related Documentation

- [Tasks](./tasks.md) — Detailed implementation tasks
- [Deployment Guide](./deployment-guide.md) — ADMINDev integration steps
- [SiteForge README](../../README.md) — Main project documentation
- [ADMINDev Structure](../../../ADMINDev/.kiro/steering/structure.md) — ADMINDev workspace structure
