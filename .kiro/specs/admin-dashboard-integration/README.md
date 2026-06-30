# SiteForge Admin Dashboard Integration Spec

**Status**: Phase 1 Complete ✅ | Phases 2-4 Pending  
**Created**: June 30, 2026  
**Workspace**: /workspace/siteforge

---

## Quick Summary

This spec defines the complete implementation of a webmaster dashboard for the SiteForge multi-site platform, accessible at `siteforge.YOURADMINDOMAIN.com`. The dashboard provides real-time visibility into all deployed client sites with instant status checks, configuration overview, and quick-access links.

---

## What's Included

### 📋 Documentation
- **overview.md** — Architecture, features, and requirements
- **tasks.md** — Detailed task breakdown across 4 phases
- **deployment-guide.md** — Step-by-step ADMINDev integration guide
- **README.md** — This file

### ✅ Phase 1: Complete
- **CLI Command**: `python -m cli.siteforge dashboard`
- **Output**: Self-contained static HTML at `apps/admin/siteforge-dashboard.html`
- **Features**: Site metadata, optional health checks, modern UI
- **Status**: ✅ Tested and working

---

## Quick Start

### Generate Dashboard Locally

```bash
cd /workspace/siteforge

# Basic dashboard (no health checks)
python -m cli.siteforge dashboard

# With live site status checks
python -m cli.siteforge dashboard --ping

# Custom output path
python -m cli.siteforge dashboard --output /custom/path.html
```

### View Generated Dashboard

```bash
# Open in browser
open apps/admin/siteforge-dashboard.html

# Or serve locally
python -m http.server --directory apps/admin 8000
# Visit: http://localhost:8000/siteforge-dashboard.html
```

---

## Dashboard Features

### Site Cards Display
Each site shows:
- 🌍 **Site Name** — Branded name (e.g., "Serenity Therapy")
- 🔗 **Domain** — Clickable link to site homepage
- 👨‍💼 **Admin URL** — Quick link to admin panel (domain + `/admin`)
- 🗣️ **Default Language** — Primary language code
- 🌐 **Supported Languages** — Badges for all enabled languages
- 🧩 **Active Modules** — Badges for installed features
- ⏰ **Last Updated** — Config file modification timestamp

### Status Indicators (Optional)
When using `--ping` flag:
- 🟢 **Online** — Site responsive to `/api/config` endpoint
- 🔴 **Offline** — Site unreachable or timed out
- ⚪ **Unknown** — Ping checks disabled

### Summary Stats
- Number of sites currently online
- Number of sites offline
- Total configured sites

---

## Architecture

```
User Browser
    ↓
https://siteforge.YOURADMINDOMAIN.com (DNS via Route53)
    ↓
CloudFront Distribution (CDN + HTTPS)
    ↓
ADMINDev Next.js Application
    ↓
Static HTML Dashboard (Self-contained, ~8-50KB)
```

---

## Implementation Status

| Phase | Task | Status | Est. Time |
|-------|------|--------|-----------|
| 1 | Dashboard command | ✅ Complete | 2h |
| 2.1 | ADMINDev route creation | 🔄 Pending | 1h |
| 2.2 | DNS configuration | 🔄 Pending | 30m |
| 2.3 | CI/CD automation | 🔄 Pending | 1h |
| 3.1 | Authentication (opt) | 🔄 Pending | 2h |
| 4.1 | Full deployment | 🔄 Pending | 2h |
| 4.2 | Documentation | 🔄 Pending | 1h |
| **Total** | | | **~9.5h** |

---

## Files Modified/Created

### New Files
```
cli/siteforge/commands/dashboard.py          ← Dashboard command implementation
apps/admin/siteforge-dashboard.html          ← Generated output (auto-created)
.kiro/specs/admin-dashboard-integration/     ← This spec
  ├── README.md
  ├── overview.md
  ├── tasks.md
  └── deployment-guide.md
```

### Modified Files
```
cli/siteforge/__main__.py                    ← Added dashboard command registration
```

---

## Key Technical Decisions

### 1. Static HTML Generation
✅ **Why**: No build step, instant deployment, CDN-friendly  
✅ **How**: Python template generation with inline CSS  
✅ **Benefit**: 8KB file, <1s load time, works everywhere

### 2. Optional Health Checks
✅ **Why**: Real-time visibility without strict requirements  
✅ **How**: Concurrent requests with 3s timeout per site  
✅ **Benefit**: Shows status without blocking dashboard generation

### 3. Self-Contained HTML
✅ **Why**: No external dependencies or CSS frameworks  
✅ **How**: All styling inlined, no JavaScript  
✅ **Benefit**: Works in restricted environments, fast loading

### 4. Subdomain Integration
✅ **Why**: Separates internal tools from public platform  
✅ **How**: Route53 CNAME to ADMINDev CloudFront  
✅ **Benefit**: Clean URL, single certificate, familiar domain

---

## Security Model

### Current (Phase 1)
- ✅ Read-only (scans local config files)
- ✅ No API keys or secrets exposed
- ✅ No database access
- ✅ Static HTML (no execution)
- ⚠️ No authentication (internal tool)

### Phase 2+ (Optional)
- Optional JWT authentication
- IP whitelisting
- Audit logging
- Rate limiting

---

## Performance Targets

| Metric | Target | Expected |
|--------|--------|----------|
| Page Load | <1s | ~500ms via CDN |
| Dashboard Generation | <5s | ~1s (10 sites) |
| Health Checks | <40s | ~30s (10 sites @3s ea) |
| File Size | <100KB | ~8KB (1 site), ~50KB (10 sites) |
| Mobile Load | <2s | ~1.5s on 4G |

---

## Next Steps

### Immediate (When Ready)
1. ✅ Phase 1 complete — Dashboard command working
2. 🔄 Create ADMINDev route to serve dashboard
3. 🔄 Configure DNS for subdomain
4. 🔄 Set up SSL certificate

### Short-term (1-2 weeks)
5. 🔄 Test full deployment
6. 🔄 Set up automated generation
7. 🔄 Launch to production

### Future (Optional)
8. Add authentication layer
9. Implement historical trending
10. Add export reports (PDF/CSV)
11. Integrate with monitoring tools

---

## Usage Examples

### Daily Webmaster Check
```bash
# Generate fresh dashboard
python -m cli.siteforge dashboard --ping

# Open in browser
open apps/admin/siteforge-dashboard.html

# See: Status of all sites, quick links to each admin panel
```

### Before Deployment
```bash
# Verify all sites' configs are correct
python -m cli.siteforge list

# Generate dashboard with health checks
python -m cli.siteforge dashboard --ping

# Commit generated HTML to repo
git add apps/admin/siteforge-dashboard.html
git commit -m "chore: update dashboard"
```

### Production Monitoring
```bash
# Automated via GitHub Actions every hour
# Generates dashboard, checks all sites, commits changes
# Dashboard automatically deployed to siteforge.YOURADMINDOMAIN.com
```

---

## Testing Checklist

### Local Testing ✅
- [x] Dashboard command runs: `python -m cli.siteforge dashboard`
- [x] HTML file generated: `apps/admin/siteforge-dashboard.html`
- [x] File size reasonable: ~8KB
- [x] HTML valid and renders
- [x] --ping flag works: `python -m cli.siteforge dashboard --ping`
- [x] Custom output path works: `--output /custom/path.html`
- [x] Help text clear: `python -m cli.siteforge dashboard --help`

### ADMINDev Integration 🔄 (Pending Phase 2)
- [ ] Route created in Next.js
- [ ] Dashboard loads at /siteforge-dashboard
- [ ] All links functional
- [ ] Mobile responsive
- [ ] No console errors

### Deployment 🔄 (Pending Phase 3)
- [ ] DNS resolves: `dig siteforge.YOURADMINDOMAIN.com`
- [ ] HTTPS works: `curl -I https://siteforge.YOURADMINDOMAIN.com`
- [ ] Dashboard accessible
- [ ] CloudFront caching working
- [ ] Performance <1s load

### Production 🔄 (Pending Phase 4)
- [ ] Automated generation working
- [ ] CI/CD pipeline updated
- [ ] Monitoring alerts configured
- [ ] Team trained
- [ ] Documentation complete

---

## Troubleshooting

### Dashboard command fails
```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check dependencies
pip list | grep -E "typer|rich|requests"

# Reinstall
pip install -r requirements.txt
```

### No site configs found
```bash
# Check sites directory
ls -la sites/

# Check site-config.json exists
find sites -name "site-config.json"
```

### Health checks timeout
```bash
# Test site manually
curl -I https://serenity-therapy.com/api/config

# Increase timeout in dashboard.py (line ~54)
timeout: 5  # Instead of 3
```

See **deployment-guide.md** for more troubleshooting.

---

## Documentation Map

| Document | Purpose | Audience |
|----------|---------|----------|
| **overview.md** | Architecture & features | Everyone |
| **tasks.md** | Detailed task breakdown | Developers |
| **deployment-guide.md** | Step-by-step deployment | DevOps/SRE |
| **README.md** | Quick reference | Everyone |

---

## Key Metrics

### Phase 1 Completion
- ✅ Command implemented and tested
- ✅ HTML generation working
- ✅ Health checks functional
- ✅ Self-contained file (<100KB)
- ✅ CLI registered

### Ready for Phase 2
- Dashboard command production-ready
- Output stable and tested
- Ready for ADMINDev integration

---

## Sign-Off

**Phase 1**: Complete and verified  
**Status**: Ready for ADMINDev integration (Phase 2)  
**Next Action**: Create ADMINDev route (Task 2.1)

---

## Questions?

Refer to:
1. **overview.md** — For "what" and "why"
2. **tasks.md** — For detailed breakdown
3. **deployment-guide.md** — For "how to" deploy
4. **Local testing** — Run command and verify output

For issues, create GitHub issue with `[dashboard]` label.

---

**Last Updated**: June 30, 2026  
**Version**: 1.0  
**Status**: Phase 1 Complete, Phases 2-4 Pending
