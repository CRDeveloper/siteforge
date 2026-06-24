# CLI Commands: Destroy & Add-Module

## Overview

Two new CLI commands complete Priority 1:

- **`siteforge destroy`** — Decommission a site (tear down AWS resources + cleanup SSM)
- **`siteforge add-module`** — Add optional modules to an existing site

---

## `siteforge destroy --id X`

Completely removes a site: tears down CDK stacks, deletes SSM parameters, removes local config.

### Usage

```bash
siteforge destroy --id serenity-therapy
siteforge destroy --id serenity-therapy --force  # Skip confirmation
```

### Workflow

1. **Confirmation prompt** (unless `--force` flag)
   - Shows warning about permanent destruction
   - Lists what will be deleted: AWS resources, SSM params, local directory

2. **CDK Destroy**
   - Runs `cdk destroy SfSiteStack-{site_id} --force`
   - Removes: S3, CloudFront, DynamoDB, Lambda, API Gateway, etc.
   - Continues if stack doesn't exist

3. **SSM Cleanup**
   - Deletes `/siteforge/{site_id}/jwt_secret`
   - Deletes `/siteforge/{site_id}/brevo_api_key`
   - Handles missing parameters gracefully

4. **Local Removal**
   - Removes `sites/{site_id}/` directory
   - Cleans up site config and all local files

### Example Output

```
SiteForge — Destroying site: serenity-therapy

→ Destroying CDK stack: SfSiteStack-serenity-therapy
✓ CDK stack destroyed
→ Cleaning up SSM parameters
  ✓ Deleted /siteforge/serenity-therapy/jwt_secret
  ✓ Deleted /siteforge/serenity-therapy/brevo_api_key
→ Removing local site directory
✓ Removed /workspace/siteforge/sites/serenity-therapy

✓ Destruction Complete
Site destroyed: serenity-therapy

All AWS resources and configuration have been removed.
```

---

## `siteforge add-module --id X --module Y`

Add optional modules (payments, WhatsApp, analytics, etc.) to a site and redeploy.

### Available Modules

| Module | Description |
|---|---|
| `payments` | Stripe payment processing for bookings |
| `whatsapp` | WhatsApp notifications via Brevo |
| `blog` | Markdown-based blog with S3 storage |
| `gallery` | Photo gallery with S3 backend |
| `analytics` | Plausible or CloudWatch analytics |
| `sms` | SMS notifications (Twilio or Brevo) |

### Usage

```bash
siteforge add-module --id serenity-therapy --module payments
siteforge add-module --id serenity-therapy --module analytics --region us-west-2
```

### Workflow

1. **Validate module**
   - Check if module is in `AVAILABLE_MODULES`
   - Verify site config exists
   - Prevent duplicate modules

2. **Update site-config.json**
   - Append module to `modules[]` array
   - Keep modules sorted alphabetically

3. **Module-specific setup**
   - `payments`: Add Stripe config stub (publishableKey, webhookSecret)
   - `whatsapp`: Set `whatsapp.enabled = true`
   - `analytics`: Add provider config (plausible or cloudwatch)

4. **CDK Redeploy**
   - Runs `cdk deploy SfSiteStack-{site_id} --require-approval never`
   - Updates Lambda function code with new module handlers

### Example Output

```
SiteForge — Adding module: payments
  Site:   serenity-therapy
  Module: Stripe payment processing for bookings

→ Updating site-config.json
✓ Added 'payments' to modules list
✓ Added Stripe config (requires webhook secret)
→ Deploying CDK stack with new module
✓ CDK stack updated

✓ Module Added
Module added: payments

Current modules:
  • admin-dashboard
  • appointments
  • file-uploads
  • notifications
  • payments
  • user-auth

Lambda functions have been updated. Changes take effect immediately.
```

---

## Implementation Details

### Files Created

| File | LOC | Purpose |
|---|---|---|
| `cli/siteforge/commands/destroy.py` | ~100 | Destroy command with CDK + SSM cleanup |
| `cli/siteforge/commands/add_module.py` | ~130 | Add module command with config updates |
| **Updated** `cli/siteforge/__main__.py` | | Import both commands + register |

### Code Patterns Used

- ✓ **Rich panels** for visual feedback (Panel with colored borders)
- ✓ **Typer options** for CLI arguments (--id, --module, --force, --region)
- ✓ **Subprocess** for CDK operations (matching existing create.py pattern)
- ✓ **JSON config** reading/writing (matching existing seed.py pattern)
- ✓ **Console printing** for progress (matching existing commands)
- ✓ **Error handling** (exit codes, try/except, graceful failures)

### Integration

- Follows existing CLI architecture (Typer, Rich console)
- Uses same paths and naming conventions as other commands
- Compatible with existing site structure
- No breaking changes to existing commands

---

## Testing

```bash
# List available modules
siteforge add-module --id invalid-site --module payments
# → Shows error + lists available modules

# Add valid module
siteforge add-module --id serenity-therapy --module analytics

# Destroy with confirmation
siteforge destroy --id serenity-therapy
# → Prompts before destroying

# Destroy with force flag
siteforge destroy --id serenity-therapy --force
# → Skips confirmation
```

---

## Priority 1 Complete ✅

| Task | Status |
|---|---|
| CLI: destroy command | ✅ |
| CLI: add-module command | ✅ |
| Imports + registration | ✅ |
| Documentation | ✅ |

Platform is now feature-complete with full site lifecycle management (create → seed → add-module → destroy).
