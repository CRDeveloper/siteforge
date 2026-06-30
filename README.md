# SiteForge

> Multi-site appointment booking platform — AWS serverless, Next.js frontend, Python Lambda backend.
> Under $10/month per cluster · Multi-language · Themeable · WordPress-style installer.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (static export → S3 + CloudFront) |
| Backend | Python 3.12 Lambda + API Gateway v2 |
| Database | DynamoDB (single-table per site) |
| Email | Brevo (transactional + inbox + campaigns) |
| DNS | Cloudflare |
| SSL | ACM (free) |
| IaC | AWS CDK v2 (Python) |
| CLI | siteforge (Python + Typer) |
| CI/CD | GitHub Actions |

---

## Repository Structure

cd /workspace/siteforge

```
siteforge/
├── apps/
│   ├── api/                            # Python Lambda — all backend handlers
│   │   ├── main.py                     # Router entry point
│   │   ├── handlers/                   # auth, appointments, admin, public
│   │   ├── middleware/                 # JWT auth, CORS
│   │   └── lib/                        # db, email, response helpers
│   └── frontend/                       # Next.js app
│       └── src/
│           ├── app/                    # App Router pages
│           │   ├── (public)/           # Landing page, booking flow
│           │   ├── (auth)/             # Login, register, reset
│           │   ├── (user)/             # Appointments dashboard
│           │   └── (admin)/            # Admin panel
│           ├── components/             # UI components
│           ├── i18n/                   # Translations (EN + ES)
│           └── lib/                    # API client, Zustand store
├── infra/
│   └── cdk/                            # CDK v2 stacks
│       ├── app.py                      # CDK app entry point
│       └── stacks/
│           ├── shared_stack.py         # Shared IAM policies, SSM
│           └── site_stack.py           # Per-site: S3, CF, DynamoDB, Lambda, APIGW
├── cli/
│   └── siteforge/                      # siteforge CLI tool
│       ├── commands/                   # create, deploy, config, list, seed, destroy, dashboard
│       └── __main__.py                 # CLI entry point
├── sites/
│   └── serenity-therapy/               # Sample client site
│       └── site-config.json            # All site settings
├── apps/admin/
│   └── siteforge-dashboard.html        # Generated admin dashboard (auto-created)
├── .kiro/specs/
│   └── admin-dashboard-integration/    # Admin dashboard spec & tasks
└── .github/
    └── workflows/
        └── deploy.yml                  # CI/CD — auto deploy on push
```

---

## Quick Start

### Prerequisites

```bash
# AWS CLI configured with your account
aws configure

# Node.js 20+, Python 3.12+, CDK v2
npm install -g aws-cdk
pip install aws-cdk-lib constructs typer rich boto3
```

### 1. Clone and install

```bash
git clone https://github.com/yourorg/siteforge.git
cd siteforge
npm install
```

### 2. Deploy shared infrastructure (once)

```bash
cd infra/cdk
cdk deploy SiteForgeShared
```

### 3. Create a new client site

```bash
python -m cli.siteforge create \
  --id serenity-therapy \
  --domain serenity-therapy.com \
  --admin admin@serenity-therapy.com \
  --name "Serenity Therapy" \
  --color "#5c7a6e"
```

### 4. Add secrets to SSM

```bash
# Brevo API key (from Brevo dashboard → Settings → API Keys)
aws ssm put-parameter \
  --name /siteforge/serenity-therapy/brevo_api_key \
  --value "xkeysib-..." \
  --type SecureString

# JWT secret (auto-generated during create, but you can rotate it)
aws ssm put-parameter \
  --name /siteforge/serenity-therapy/jwt_secret \
  --value "$(openssl rand -base64 64)" \
  --type SecureString
```

### 5. Configure Cloudflare DNS

After CDK outputs the CloudFront domain, add these records in Cloudflare (DNS only — no proxy):

```
CNAME  @    <id>.cloudfront.net   (DNS only ☁️)
CNAME  www  <id>.cloudfront.net   (DNS only ☁️)
```

Validate the ACM certificate by adding the CNAME record shown in AWS Console → ACM.

### 6. Set up Brevo

Follow `docs/02-brevo-setup-guide.md` to:
- Verify your sending domain
- Create the 8 email templates
- Configure the Conversations inbox

### 7. Deploy frontend

```bash
python -m cli.siteforge deploy --id serenity-therapy
```

### 8. Seed default data

```bash
python -m cli.siteforge seed --id serenity-therapy
```

---

## Adding a Second Site

```bash
python -m cli.siteforge create \
  --id my-salon \
  --domain my-salon.com \
  --admin owner@my-salon.com \
  --name "My Salon" \
  --color "#8b4513"

# List all sites
python -m cli.siteforge list
```

Each site gets completely isolated AWS resources — separate DynamoDB table,
S3 bucket, CloudFront distribution, and Lambda function.

---

## GitHub Actions CI/CD

Set these secrets in your GitHub repository:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user with CDK + S3 + CloudFront permissions |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret |
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |

Push to `main` → GitHub Actions automatically detects which sites changed and deploys only those.

---

## Common Commands

```bash
# Generate admin dashboard (lists all sites)
python -m cli.siteforge dashboard

# Generate dashboard with live health checks (3s timeout per site)
python -m cli.siteforge dashboard --ping

# Update a site's theme color
python -m cli.siteforge config --id serenity-therapy --set theme.primaryColor=#3b82f6

# Deploy only frontend (skip CDK)
python -m cli.siteforge deploy --id serenity-therapy

# View all configured sites
python -m cli.siteforge list

# Local frontend dev (hot reload)
SITE_ID=serenity-therapy npm run dev -w apps/frontend

# Run API tests
cd apps/api && pytest tests/ -v
```

---

## Admin Dashboard

The CLI includes a dashboard command that generates a static HTML status page for all configured sites:

```bash
# Generate dashboard at apps/admin/siteforge-dashboard.html
python -m cli.siteforge dashboard

# With optional health checks
python -m cli.siteforge dashboard --ping

# Custom output path
python -m cli.siteforge dashboard --output /custom/path/dashboard.html
```

The dashboard displays:
- Site name, domain, and admin URL (clickable links)
- Default and supported languages
- Active modules and features
- Last configuration update timestamp
- Optional online/offline status (with --ping flag)

See `.kiro/specs/admin-dashboard-integration/` for complete specification and deployment guide.

---

## Integration with Admin Platform

### Standalone Admin Portal (Recommended)

Deploy the dashboard HTML to your admin domain (`siteforge.YOURADMINDOMAIN.com`):

1. Generate dashboard: `python -m cli.siteforge dashboard`
2. Serve `apps/admin/siteforge-dashboard.html` via your web server
3. Configure DNS CNAME to point to your CloudFront distribution
4. Optional: Add authentication middleware for internal teams only

See `.kiro/specs/admin-dashboard-integration/deployment-guide.md` for detailed steps.


---

## Cost Estimate

~$2/site/month at < 1,000 users/month. See full breakdown in `docs/03-platform-spec-v1.1.md`.

---

## Documentation

### Platform & Architecture
- `docs/platform-spec.md` — Requirements, Architecture & Implementation Spec
- `docs/03-platform-spec-v1.1.md` — Full platform specification
- `README.md` (this file) — Getting started & quick reference

### Setup & Deployment
- `docs/01-ses-production-access-request.md` — AWS SES sandbox removal template
- `docs/02-brevo-setup-guide.md` — Brevo onboarding for each client
- `docs/04-session-recap-and-next-steps.md` — IDE Setup & Next Steps

### Admin Dashboard
- `.kiro/specs/admin-dashboard-integration/README.md` — Quick start guide
- `.kiro/specs/admin-dashboard-integration/overview.md` — Architecture & features
- `.kiro/specs/admin-dashboard-integration/tasks.md` — Implementation tasks
- `.kiro/specs/admin-dashboard-integration/deployment-guide.md` — Deployment steps
- `.kiro/specs/admin-dashboard-integration/COMPLETION_SUMMARY.md` — Phase 1 summary
