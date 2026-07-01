# SiteForge Automation Setup Guide

Complete guide for using the SiteForge automation scripts for CDK deployment, multi-site management, local development, and Slack notifications.

---

## Quick Start

### 1. Initial Setup (One-Time)

```bash
cd /workspace/siteforge

# Copy environment template
cp .env.example .env

# Edit .env with your AWS account ID and region
nano .env

# Run bootstrap setup
./scripts/setup.sh
```

### 2. Create First Site

```bash
./scripts/manage.sh create serenity-therapy \
  --domain serenity-therapy.com \
  --admin admin@serenity-therapy.com \
  --name "Serenity Therapy" \
  --color "#5c7a6e"
```

### 3. Deploy Site

```bash
./scripts/manage.sh deploy serenity-therapy
```

### 4. Local Development

```bash
./scripts/manage.sh local serenity-therapy
# Starts dev server on http://localhost:7000
```

---

## Port Allocation

Ports are chosen to avoid conflicts with other projects in the workspace:

| Project | Service | Port | Range |
|---------|---------|------|-------|
| **SiteForge** | Frontend Dev | 7000 | (non-conflicting) |
| **SiteForge** | API Local | 8200 | (non-conflicting) |

**Note**: Ports are managed automatically by the scripts. To manually free a port:
```bash
./scripts/manage.sh cleanup
```

---

## Scripts Overview

### 1. `scripts/setup.sh` — One-Time Bootstrap

Initializes SiteForge for first use. Runs once per developer/environment.

**What it does:**
- ✅ Checks prerequisites (Python, Node, AWS CLI, git)
- ✅ Validates AWS credentials
- ✅ Installs dependencies (npm, pip, CDK)
- ✅ Bootstraps CDK for your AWS account/region
- ✅ Deploys shared infrastructure stack
- ✅ Generates local HTTPS certificates (optional)

**Usage:**
```bash
./scripts/setup.sh
```

**Output:**
```
🚀 SiteForge Bootstrap Setup
════════════════════════════════════════════════════════════════

ℹ Checking Prerequisites
✓ Python 3.12 found
✓ Node.js v20.11.0 found
✓ npm 10.2.4 found
✓ AWS CLI 2.15.0 found
✓ git found
✓ AWS credentials configured (Account: 123456789012)
✓ All prerequisites installed

... [more setup steps] ...

✅ Setup Complete!
```

**When to re-run:**
- First time setup only
- If prerequisites change
- After AWS credential rotation

---

### 2. `scripts/manage.sh` — Main Orchestration

Primary interface for all SiteForge operations.

**Commands:**

#### `manage.sh init`
Re-run bootstrap setup (same as `setup.sh`)

#### `manage.sh create <site-id> [OPTIONS]`
Create a new site

**Options:**
- `--domain DOMAIN` — Domain name (required)
- `--admin EMAIL` — Admin email (required)
- `--name NAME` — Display name (required)
- `--color COLOR` — Theme color hex code (optional, default: #3b82f6)

**Example:**
```bash
./scripts/manage.sh create my-salon \
  --domain my-salon.com \
  --admin owner@my-salon.com \
  --name "My Salon" \
  --color "#e74c3c"
```

**What it does:**
- ✅ Validates site configuration
- ✅ Creates DynamoDB table
- ✅ Creates S3 buckets (frontend + logs)
- ✅ Creates CloudFront distribution
- ✅ Creates Lambda function for API
- ✅ Creates API Gateway
- ✅ Stores secrets in AWS Secrets Manager
- ✅ Sends Slack notification (if enabled)

#### `manage.sh deploy <site-id>`
Deploy/redeploy frontend to CloudFront

**Example:**
```bash
./scripts/manage.sh deploy serenity-therapy
```

**What it does:**
- ✅ Builds Next.js frontend
- ✅ Syncs to S3
- ✅ Invalidates CloudFront cache
- ✅ Shows deployment status
- ✅ Sends Slack notification (if enabled)

#### `manage.sh local <site-id>`
Start local development environment

**Example:**
```bash
./scripts/manage.sh local serenity-therapy
```

**What it does:**
- ✅ Cleans up existing processes on port 7000
- ✅ Installs dependencies
- ✅ Starts Next.js dev server on http://localhost:7000
- ✅ Supports hot-reload and file changes
- ✅ Gracefully shuts down on Ctrl+C

**Port:** http://localhost:7000 (or https:// if certificates present)

#### `manage.sh status`
Show all configured sites and status

**Example:**
```bash
./scripts/manage.sh status
```

**Output:**
```
📊 SiteForge Status
════════════════════════════════════════════════════════════════

ℹ Total sites: 2

SiteForge — Configured Sites
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━┓
┃ Site ID       ┃ Domain          ┃ Name        ┃ Lang ┃ Mods  ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━┩
│ serenity...   │ serenity...     │ Serenity... │ en   │ auth  │
│ my-salon      │ my-salon.com    │ My Salon    │ en   │ auth  │
└───────────────┴─────────────────┴─────────────┴──────┴───────┘

ℹ AWS Infrastructure:
  Region:  us-east-1
  Account: 123456789012
```

#### `manage.sh logs <site-id>`
View recent logs for a site

**Example:**
```bash
./scripts/manage.sh logs serenity-therapy
```

**What it does:**
- ✅ Retrieves CloudWatch logs
- ✅ Shows Lambda error logs
- ✅ Displays recent activity

#### `manage.sh config <site-id> [--set KEY=VALUE]`
View or edit site configuration

**Examples:**
```bash
# View current config
./scripts/manage.sh config serenity-therapy

# Edit a value
./scripts/manage.sh config serenity-therapy --set theme.primaryColor=#3b82f6
```

#### `manage.sh cleanup`
Stop local servers and free ports

**Example:**
```bash
./scripts/manage.sh cleanup
```

**What it does:**
- ✅ Kills processes on port 7000 (Next.js)
- ✅ Kills processes on port 8200 (API)
- ✅ Stops npm dev processes
- ✅ Frees all resources

#### `manage.sh destroy <site-id>`
⚠️ **IRREVERSIBLE** — Destroy a site and all AWS resources

**Example:**
```bash
./scripts/manage.sh destroy serenity-therapy
```

**What it does:**
- ⚠️ Deletes CloudFormation stack
- ⚠️ Deletes all AWS resources (Lambda, S3, DynamoDB, CloudFront)
- ⚠️ Deletes site configuration
- ✅ Requires confirmation (type site ID to confirm)
- ✅ Sends Slack notification (if enabled)

#### `manage.sh help`
Show help and usage information

---

### 3. `scripts/slack_notifier.py` — Slack Integration

Python utility for sending Slack notifications about deployments.

**Notifications sent for:**
- 🚀 Deployment started
- ✅ Deployment completed
- ❌ Deployment failed (with step and error)
- ✨ Site created
- 🗑️ Site destroyed

**Setup:**

1. **Create Slack Webhook**
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - Name: "SiteForge Notifier"
   - Select workspace
   - Enable "Incoming Webhooks"
   - Click "Add New Webhook to Workspace"
   - Copy the webhook URL

2. **Store in AWS Secrets Manager**
   ```bash
   aws secretsmanager create-secret \
     --name siteforge/slack-webhook-url \
     --secret-string "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. **Enable in .env**
   ```bash
   SLACK_NOTIFICATIONS_ENABLED=true
   SLACK_SECRET_NAME=siteforge/slack-webhook-url
   SLACK_REGION=us-east-1
   ```

4. **Test**
   ```bash
   python3 scripts/slack_notifier.py
   ```

**Environment Variables:**
```bash
SLACK_NOTIFICATIONS_ENABLED=true          # Enable/disable
SLACK_SECRET_NAME=siteforge/slack-webhook-url  # Secret in Secrets Manager
SLACK_REGION=us-east-1                    # AWS region
```

**Disable notifications:**
```bash
SLACK_NOTIFICATIONS_ENABLED=false
```

---

## Environment Configuration (.env)

Copy `.env.example` to `.env` and customize:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Primary Demo Site
PRIMARY_SITE_ID=serenity-therapy

# Local Development Ports (non-conflicting)
FRONTEND_PORT=7000
API_PORT=8200

# Local HTTPS (optional)
ENABLE_LOCAL_HTTPS=true

# Slack Integration (optional)
SLACK_NOTIFICATIONS_ENABLED=false
SLACK_SECRET_NAME=siteforge/slack-webhook-url
SLACK_REGION=us-east-1

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
```

---

## Workflow Examples

### Example 1: Complete Setup & Deploy

```bash
# 1. Initial bootstrap (one-time)
./scripts/setup.sh

# 2. Create demo site
./scripts/manage.sh create serenity-therapy \
  --domain serenity-therapy.com \
  --admin admin@serenity-therapy.com \
  --name "Serenity Therapy"

# 3. Configure Brevo (email service)
# Follow: docs/02-brevo-setup-guide.md

# 4. Deploy site
./scripts/manage.sh deploy serenity-therapy

# 5. View deployment status
./scripts/manage.sh status
```

**Result:**
- ✅ Site live at https://serenity-therapy.com
- ✅ Admin panel at https://serenity-therapy.com/admin
- ✅ All AWS resources created
- ✅ Slack notification sent (if enabled)

### Example 2: Local Development

```bash
# 1. Start local dev environment
./scripts/manage.sh local serenity-therapy

# 2. Open browser
# http://localhost:7000 (or https:// with certificates)

# 3. Make code changes
# Changes auto-reload in browser

# 4. Stop dev server (Ctrl+C)

# 5. Cleanup ports
./scripts/manage.sh cleanup
```

### Example 3: Multiple Sites

```bash
# Create second site
./scripts/manage.sh create my-salon \
  --domain my-salon.com \
  --admin owner@my-salon.com \
  --name "My Salon" \
  --color "#e74c3c"

# Deploy both
./scripts/manage.sh deploy serenity-therapy
./scripts/manage.sh deploy my-salon

# View all sites
./scripts/manage.sh status

# Local dev on salon site
./scripts/manage.sh local my-salon
```

### Example 4: Enable Slack Notifications

```bash
# 1. Create Slack webhook (see Slack section above)

# 2. Store in Secrets Manager
aws secretsmanager create-secret \
  --name siteforge/slack-webhook-url \
  --secret-string "https://hooks.slack.com/..."

# 3. Enable in .env
sed -i 's/SLACK_NOTIFICATIONS_ENABLED=false/SLACK_NOTIFICATIONS_ENABLED=true/' .env

# 4. Deploy (notifications will be sent)
./scripts/manage.sh deploy serenity-therapy
# ✅ Slack notification sent to channel
```

---

## Troubleshooting

### Setup fails with "AWS credentials not found"

**Solution:**
```bash
# Configure AWS CLI
aws configure

# Or export credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Verify
aws sts get-caller-identity
```

### Port 7000 already in use

**Solution:**
```bash
# Free all ports
./scripts/manage.sh cleanup

# Or manually
fuser -k 7000/tcp 8200/tcp
```

### Local dev won't start

**Solution:**
```bash
# Check for node_modules
cd apps/frontend
npm install

# Clean Next.js cache
rm -rf .next

# Try again
./scripts/manage.sh local serenity-therapy
```

### Deployment fails at "Frontend Build"

**Solution:**
```bash
# Check Node.js version
node --version  # Should be 20+

# Reinstall dependencies
cd apps/frontend
npm install

# Try deploying again
cd ../..
./scripts/manage.sh deploy serenity-therapy
```

### CDK bootstrap fails

**Solution:**
```bash
# Clear CDK cache
cd infra/cdk
rm -rf cdk.out .parcel-cache node_modules
npm install

# Bootstrap again
./scripts/setup.sh
```

### Slack notifications not sending

**Solution:**
```bash
# Verify secret exists
aws secretsmanager describe-secret \
  --secret-id siteforge/slack-webhook-url

# Test notifier
python3 scripts/slack_notifier.py

# Check .env
grep SLACK .env

# Verify webhook URL is correct
aws secretsmanager get-secret-value \
  --secret-id siteforge/slack-webhook-url \
  --query SecretString
```

---

## Project Structure

```
/workspace/siteforge/
├── scripts/
│   ├── setup.sh                  ← Bootstrap (one-time)
│   ├── manage.sh                 ← Main orchestration
│   ├── slack_notifier.py         ← Slack integration
│   └── verify-features.sh        ← Verification (existing)
├── .env.example                  ← Environment template
├── .env                          ← Your configuration (git-ignored)
├── infra/
│   └── cdk/                      ← Infrastructure as Code
├── apps/
│   ├── frontend/                 ← Next.js frontend
│   └── api/                      ← Python API
├── cli/
│   └── siteforge/                ← CLI tool
├── sites/
│   └── serenity-therapy/         ← Demo site config
└── logs/                         ← Generated logs
```

---

## Performance Tips

1. **Faster deployments:**
   - Use `--skip-build` flag (for frontend-only updates)
   - Reuse Docker images
   - Enable CloudFront caching

2. **Faster local development:**
   - Keep `node_modules` installed
   - Use `npm ci` instead of `npm install`
   - Enable file watching on fast disk

3. **Reduce costs:**
   - Use on-demand scaling for Lambda
   - Delete unused sites with `destroy`
   - Consolidate multiple environments

---

## Security Best Practices

1. **AWS Credentials:**
   - Use IAM users (not root)
   - Enable MFA
   - Rotate keys regularly
   - Never commit `.env` (use `.gitignore`)

2. **Slack Webhooks:**
   - Store in Secrets Manager (not .env)
   - Restrict webhook permissions
   - Rotate webhooks periodically

3. **Site Secrets:**
   - Store API keys in Secrets Manager
   - Never commit secrets
   - Use environment variables

4. **Local Development:**
   - Use self-signed HTTPS locally (included)
   - Don't expose `.env` to public networks
   - Clean up ports and processes after dev

---

## Next Steps

After initial setup:

1. ✅ Run bootstrap: `./scripts/setup.sh`
2. ✅ Create first site: `./scripts/manage.sh create ...`
3. ✅ Configure email: See `docs/02-brevo-setup-guide.md`
4. ✅ Deploy site: `./scripts/manage.sh deploy ...`
5. ✅ Local development: `./scripts/manage.sh local ...`
6. 🔄 Optional: Enable Slack notifications
7. 🔄 Optional: Create additional sites

---

## Support

For issues:
1. Check troubleshooting section above
2. Review logs: `tail -f logs/siteforge.log`
3. Check AWS CloudFormation: `aws cloudformation list-stacks`
4. Review CDK output: `infra/cdk/cdk.out/`

---

## Reference

- **SiteForge Main**: `README.md`
- **Specification**: `.kiro/specs/admin-dashboard-integration/`
- **Brevo Setup**: `docs/02-brevo-setup-guide.md`
- **Platform Spec**: `docs/03-platform-spec-v1.1.md`
- **AWS CDK**: https://docs.aws.amazon.com/cdk/v2/guide/
- **Slack API**: https://api.slack.com/

---

**Last Updated**: June 30, 2026  
**Version**: 1.0  
**Status**: Production Ready
