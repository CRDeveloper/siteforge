# SiteForge Admin Dashboard Integration — Tasks

---

## Phase 1: CLI Dashboard Command ✅ COMPLETE

### Task 1.1: Create Dashboard Command Module
**Status**: ✅ DONE  
**File**: `cli/siteforge/commands/dashboard.py`

- [x] Scan `sites/*/site-config.json` files
- [x] Extract site metadata (name, domain, languages, modules)
- [x] Get file modification timestamps
- [x] Generate self-contained HTML with inline CSS
- [x] Implement optional `--ping` flag with 3s timeout
- [x] Handle errors gracefully
- [x] Output to default location: `apps/admin/siteforge-dashboard.html`
- [x] Support custom output paths via `--output` flag

**Acceptance Criteria**:
- Command runs without errors: `python -m cli.siteforge dashboard`
- Generates valid HTML file with all site information
- `--ping` flag shows site status (online/offline)
- `--output` flag allows custom paths
- Rich console output shows progress and results

**Verification**:
```bash
cd /workspace/siteforge
python -m cli.siteforge dashboard
# Check: File created at apps/admin/siteforge-dashboard.html
# Check: Open in browser, verify layout and content

python -m cli.siteforge dashboard --ping
# Check: Status indicators appear (if sites are online)

python -m cli.siteforge dashboard --output /tmp/test.html
# Check: File created at /tmp/test.html
```

---

### Task 1.2: Register Command in CLI
**Status**: ✅ DONE  
**File**: `cli/siteforge/__main__.py`

- [x] Import dashboard command
- [x] Register as `siteforge dashboard` command
- [x] Verify command appears in help: `python -m cli.siteforge --help`

**Acceptance Criteria**:
- Command listed in `--help` output
- Command description is clear
- Command runs without import errors

**Verification**:
```bash
python -m cli.siteforge --help
# Check: "dashboard" appears in command list

python -m cli.siteforge dashboard --help
# Check: Help text shows --output and --ping options
```

---

### Task 1.3: Test with Sample Site
**Status**: ✅ DONE

- [x] Generate dashboard for `serenity-therapy` site
- [x] Verify all fields populate correctly
- [x] Open HTML file in browser
- [x] Check layout, styling, links work
- [x] Test with multiple sites (add another test site if needed)

**Acceptance Criteria**:
- Dashboard generates successfully
- All site data displays correctly
- Admin links are properly formatted
- Styling renders correctly
- No console errors in browser

---

## Phase 2: ADMINDev Integration 🔄 PENDING

### Task 2.1: Create Dashboard Route in ADMINDev
**Status**: TODO  
**Files**: 
- `ADMINDev/nextjs-admin-cms/app/siteforge-dashboard/page.tsx` (or similar)
- `ADMINDev/nextjs-admin-cms/lib/dashboard-loader.ts`

**Description**: Create a Next.js page in ADMINDev that serves the SiteForge dashboard as a read-only view.

**Steps**:
- [ ] Create page component in ADMINDev Next.js app
- [ ] Add route for `/siteforge-dashboard`
- [ ] Load static HTML from siteforge workspace
- [ ] Serve with appropriate headers (no-cache for dashboard)
- [ ] Add optional authentication middleware (view-only)
- [ ] Test page loads at ADMINDev domain
- [ ] Verify all links and styling work in ADMINDev context

**Implementation Details**:
```typescript
// Example: ADMINDev/nextjs-admin-cms/app/siteforge-dashboard/page.tsx
import { readFileSync } from 'fs';
import { join } from 'path';

export default function SiteForgedDashboard() {
  const dashboardPath = join(process.cwd(), '../../siteforge/apps/admin/siteforge-dashboard.html');
  const html = readFileSync(dashboardPath, 'utf-8');
  
  return (
    <div className="w-full h-full">
      <iframe srcDoc={html} className="w-full h-full border-none" />
    </div>
  );
}
```

**Acceptance Criteria**:
- Dashboard accessible at ADMINDev domain
- All site links open in new tabs
- Styling matches dashboard theme
- Page loads without errors
- Mobile responsive

**Verification**:
```bash
# Deploy ADMINDev
cd /workspace/ADMINDev
npm run build

# Test locally
SITE_ID=test npm run dev

# Navigate to: http://localhost:3000/siteforge-dashboard
# Check: Dashboard displays
```

---

### Task 2.2: Configure DNS for Subdomain
**Status**: TODO  
**Environment**: AWS Route53 + Cloudflare

**Description**: Set up DNS routing for `siteforge.YOURADMINDOMAIN.com` to point to ADMINDev infrastructure.

**Steps**:
- [ ] Get CloudFront distribution domain from ADMINDev CDK stack
- [ ] Create Route53 record: `siteforge.YOURADMINDOMAIN.com` → CloudFront domain
- [ ] Update Cloudflare DNS (if used): Add CNAME for `siteforge`
- [ ] Test DNS resolution: `dig siteforge.YOURADMINDOMAIN.com`
- [ ] Test HTTPS certificate (ACM should auto-provision)
- [ ] Test page access at `https://siteforge.YOURADMINDOMAIN.com`

**Implementation**:
```bash
# Example: Update Route53 via AWS CLI
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "siteforge.YOURADMINDOMAIN.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "d111111abcdef8.cloudfront.net"}]
      }
    }]
  }'
```

**Acceptance Criteria**:
- DNS resolves correctly: `dig +short siteforge.YOURADMINDOMAIN.com`
- HTTPS certificate valid
- Page accessible at `https://siteforge.YOURADMINDOMAIN.com`
- Redirects work correctly

**Verification**:
```bash
# Test DNS
dig siteforge.YOURADMINDOMAIN.com
# Should return CloudFront IP

# Test HTTPS
curl -I https://siteforge.YOURADMINDOMAIN.com
# Should return 200 with SSL certificate
```

---

### Task 2.3: Set Up CI/CD Integration
**Status**: TODO  
**Files**:
- `.github/workflows/deploy.yml` (update)
- `scripts/generate-dashboard.sh` (create)

**Description**: Automate dashboard generation on each deployment.

**Steps**:
- [ ] Create shell script to generate dashboard: `scripts/generate-dashboard.sh`
- [ ] Add pre-deployment step in GitHub Actions
- [ ] Run: `cd siteforge && python -m cli.siteforge dashboard`
- [ ] Commit generated HTML to artifact store or upload to ADMINDev
- [ ] Test CI/CD pipeline generates dashboard automatically
- [ ] Verify new dashboard is live after deployment

**Script Example**:
```bash
#!/bin/bash
# scripts/generate-dashboard.sh

set -e

echo "📊 Generating SiteForge dashboard..."
cd /workspace/siteforge
python -m cli.siteforge dashboard

echo "✓ Dashboard generated at: apps/admin/siteforge-dashboard.html"
echo "📤 Dashboard ready for deployment"
```

**GitHub Actions Integration**:
```yaml
# In .github/workflows/deploy.yml
- name: Generate SiteForge Dashboard
  run: |
    cd /workspace/siteforge
    python -m cli.siteforge dashboard
    
- name: Upload Dashboard
  run: |
    # Copy to ADMINDev public directory or artifact store
    cp /workspace/siteforge/apps/admin/siteforge-dashboard.html \
       /workspace/ADMINDev/nextjs-admin-cms/public/siteforge-dashboard.html
```

**Acceptance Criteria**:
- CI/CD runs dashboard generation on each deployment
- Dashboard updates reflect latest site configs
- No pipeline failures from dashboard generation
- Dashboard deployed within 5 minutes of commit

**Verification**:
```bash
# Check GitHub Actions logs
git log --oneline
# Latest commit should show dashboard generation in workflow

# Test manually
./scripts/generate-dashboard.sh
```

---

## Phase 3: Authentication & Security (Optional) 🔄 PENDING

### Task 3.1: Implement View-Only Access Control
**Status**: TODO (Optional)  
**Files**:
- `ADMINDev/nextjs-admin-cms/middleware/dashboard-auth.ts`
- `ADMINDev/nextjs-admin-cms/app/siteforge-dashboard/page.tsx`

**Description**: Add optional authentication for dashboard access (internal teams only).

**Steps**:
- [ ] Add middleware to check JWT token
- [ ] Implement role-based access (admin/team-lead only)
- [ ] Add audit logging for dashboard views
- [ ] Create endpoint to generate dashboard preview
- [ ] Test access controls work correctly

**Acceptance Criteria**:
- Dashboard requires authentication
- Only authorized users can view
- Audit log records all views
- No sensitive data exposed

---

## Phase 4: Production Deployment 🔄 PENDING

### Task 4.1: Full Deployment Test
**Status**: TODO

- [ ] Deploy ADMINDev with dashboard route
- [ ] Verify dashboard accessible at `siteforge.YOURADMINDOMAIN.com`
- [ ] Test all site links work
- [ ] Verify health checks (if --ping enabled)
- [ ] Test on multiple devices/browsers
- [ ] Monitor CloudWatch for errors
- [ ] Load test dashboard (concurrent users)

**Acceptance Criteria**:
- Dashboard live at `siteforge.YOURADMINDOMAIN.com`
- All functionality working
- No errors in logs
- Page loads <1s
- Mobile responsive

---

### Task 4.2: Documentation & Handoff
**Status**: TODO

- [ ] Update README with dashboard access instructions
- [ ] Document dashboard features and usage
- [ ] Create troubleshooting guide
- [ ] Add screenshots to documentation
- [ ] Train internal team on dashboard
- [ ] Create runbooks for common scenarios

**Deliverables**:
- `docs/DASHBOARD_GUIDE.md` — User guide
- `docs/DASHBOARD_TROUBLESHOOTING.md` — Troubleshooting
- `README.md` update with dashboard link

---

## Dependencies & Blockers

### Phase 1 ✅ COMPLETE
- No blockers

### Phase 2
- Requires ADMINDev deployment infrastructure to be ready
- DNS records must be accessible
- CloudFront distribution must be active

### Phase 3-4
- Depends on Phase 2 completion
- Requires staging environment for testing

---

## Success Metrics

- [x] Dashboard command works locally
- [x] All site information displays correctly
- [ ] Dashboard accessible at ADMINDev domain
- [ ] Dashboard accessible at `siteforge.YOURADMINDOMAIN.com`
- [ ] Automatic generation on each deployment
- [ ] <1s page load time
- [ ] 100% mobile responsive
- [ ] 0 errors in production logs

---

## Timeline Estimate

| Phase | Task | Estimate | Status |
|-------|------|----------|--------|
| 1 | Dashboard command | 2 hours | ✅ DONE |
| 2.1 | ADMINDev route | 1 hour | TODO |
| 2.2 | DNS setup | 30 min | TODO |
| 2.3 | CI/CD integration | 1 hour | TODO |
| 3.1 | Authentication | 2 hours | TODO (Optional) |
| 4.1 | Full deployment | 2 hours | TODO |
| 4.2 | Documentation | 1 hour | TODO |
| **Total** | | **~9.5 hours** | |

---

## Notes

- Dashboard is read-only (no modifications)
- No sensitive data exposed in HTML
- All site health checks are optional
- HTML is self-contained (no external resources)
- Performance optimized for webmasters viewing multiple sites

---

## Sign-Off

Phase 1 complete. Ready to proceed with Phase 2 (ADMINDev integration) when ready.

**Next Action**: Task 2.1 — Create ADMINDev route for dashboard
