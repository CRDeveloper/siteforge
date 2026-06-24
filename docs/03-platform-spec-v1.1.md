# SiteForge Platform — Full Specification v1.1

> AWS-native multi-site appointment booking platform.  
> Under $10/month · Serverless · Multi-language · Themeable · WordPress-style installer

**Changelog from v1.0:**
- DNS updated: Cloudflare (not Route 53) for domain registration and DNS
- Email updated: Brevo as primary communication platform (replaces Zoho + SES-only approach)
- Added: Communication module spec (transactional, campaigns, WhatsApp roadmap)
- Added: Brevo → SES migration path at scale

---

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Hosting & Infrastructure Decision](#2-hosting--infrastructure-decision)
3. [System Architecture](#3-system-architecture)
4. [Feature Requirements](#4-feature-requirements)
5. [Communication Module](#5-communication-module)
6. [Data Models (DynamoDB)](#6-data-models-dynamodb)
7. [Infrastructure-as-Code Plan](#7-infrastructure-as-code-plan)
8. [The SiteForge Installer](#8-the-siteforge-installer)
9. [Implementation Task Breakdown](#9-implementation-task-breakdown)
10. [Cost Breakdown](#10-cost-breakdown)
11. [Tech Stack Summary](#11-tech-stack-summary)
12. [API Route Reference](#12-api-route-reference)

---

## 1. Project Vision

Build a **reusable, installable website platform** that:

- Hosts multiple independent websites on shared AWS infrastructure
- Each site: landing page + user portal + admin dashboard
- Core use case: service businesses accepting appointments online
- New sites deploy via a CLI installer (`siteforge create`)
- Budget target: **< $10/month total** across hosted sites

### Core Principles

| Principle | Decision |
|---|---|
| Serverless-first | Lambda + API Gateway (no EC2, no cPanel) |
| Static where possible | Next.js static export on S3 + CloudFront |
| Config-driven | Each site is a JSON config, not a code fork |
| One DynamoDB table per site | Isolated data, predictable costs |
| Communication-first | Brevo handles all email channels + future WhatsApp |
| Open extension model | Feature modules added via `siteforge add-module` |

---

## 2. Hosting & Infrastructure Decision

### Why Not cPanel/WordPress

WordPress + cPanel feels seamless for email because cPanel bundles a full mail server (Exim MTA) on the same machine. `wp_mail()` calls the local MTA with zero configuration. The tradeoffs are poor deliverability (shared IPs flagged as spam), no scalability, and a PHP-only backend. Our stack needs Python Lambda, DynamoDB, and programmatic infrastructure — cPanel is a dead end for this.

### Chosen Stack: AWS Serverless + Cloudflare + Brevo

| Layer | Service | Reason |
|---|---|---|
| CDN + SSL | CloudFront + ACM | S3 static site delivery, free SSL |
| DNS + Domains | **Cloudflare** | At-cost domains (~$9/yr), free DNS, free DDoS protection |
| Frontend | S3 (Next.js static export) | Pennies/month, infinite scale |
| Backend | API Gateway + Lambda (Python) | Pay-per-request, no idle cost |
| Database | DynamoDB | Serverless, on-demand pricing |
| File uploads | S3 (separate bucket) | Per-GB pricing, pre-signed URLs |
| Email (all channels) | **Brevo** | Transactional + inbox + campaigns + WhatsApp |
| Email (scale) | AWS SES | Migration path at high volume |

### Cloudflare vs Route 53

| | Cloudflare | Route 53 |
|---|---|---|
| Domain .com/year | ~$9 (at cost) | ~$13 |
| DNS hosting/month | **Free** | $0.50/zone |
| CDN / DDoS | **Free tier** | Separate (CloudFront) |
| API / programmable DNS | ✅ | ✅ |
| Works with CloudFront | ✅ (DNS-only mode) | ✅ |

**Use Cloudflare for DNS and domain registration. Use CloudFront for CDN/delivery.**  
Set CloudFront CNAME in Cloudflare with proxy OFF (grey cloud / DNS only).

---

## 3. System Architecture

```
┌──────────────────────────────────────────────┐
│           SHARED INFRASTRUCTURE              │
│  Cloudflare (DNS for all domains)            │
│  ACM (SSL certs, us-east-1)                  │
│  Brevo (all email communication)             │
│  AWS SSM Parameter Store (secrets)           │
└──────────────────────────────────────────────┘
              │
    ┌─────────┴──────────┐
    ▼                    ▼
┌──────────┐      ┌──────────┐     ... N sites
│  SITE A  │      │  SITE B  │
│          │      │          │
│CloudFront│      │CloudFront│
│    ↓     │      │    ↓     │
│ S3 Bucket│      │ S3 Bucket│
│(Next.js) │      │(Next.js) │
│    ↓     │      │    ↓     │
│API Gateway      │API Gateway
│    ↓     │      │    ↓     │
│ Lambda   │      │ Lambda   │
│(Python)  │      │(Python)  │
│    ↓     │      │    ↓     │
│DynamoDB  │      │DynamoDB  │
│    ↓     │      │    ↓     │
│S3 Uploads│      │S3 Uploads│
└──────────┘      └──────────┘

Both sites share:
  └── Brevo API (per-site account or sub-account)
```

### Request Flow: User Books Appointment

```
1. User visits site → CloudFront serves Next.js from S3
2. User submits booking form → POST /appointments to API Gateway
3. API Gateway → Lambda authorizer (validates JWT)
4. Lambda handler:
   a. Validates input
   b. Checks slot availability in DynamoDB
   c. Writes appointment record to DynamoDB
   d. Calls Brevo API → sends confirmation email to user
   e. Calls Brevo API → sends alert email to admin inbox
   f. Returns 200 with appointment details
5. Next.js shows confirmation screen
6. Admin sees new appointment in dashboard + Brevo inbox
7. EventBridge Scheduler → Lambda → Brevo API (reminder, 24h before)
```

---

## 4. Feature Requirements

### 4.1 Public Landing Page

| # | Requirement | Priority |
|---|---|---|
| LP-01 | Hero section with CTA (Book Now / Register) | Must |
| LP-02 | Services section (data from API/config) | Must |
| LP-03 | About / Team section | Should |
| LP-04 | Contact info + map embed | Should |
| LP-05 | Multi-language toggle | Must |
| LP-06 | Theme support (light/dark + color scheme) | Must |
| LP-07 | Mobile responsive (320px–2560px) | Must |
| LP-08 | SEO meta tags | Must |
| LP-09 | Cookie consent banner | Should |

### 4.2 User Auth

| # | Requirement | Priority |
|---|---|---|
| AU-01 | Register with email + password | Must |
| AU-02 | Email verification (Brevo transactional) | Must |
| AU-03 | Login / Logout (JWT, httpOnly cookie) | Must |
| AU-04 | Password reset via email | Must |
| AU-05 | User profile page | Should |
| AU-06 | Social login (Google OAuth) | Could |

### 4.3 Appointment Booking (User)

| # | Requirement | Priority |
|---|---|---|
| AP-01 | Browse services | Must |
| AP-02 | Select date/time from available slots | Must |
| AP-03 | Submit appointment request | Must |
| AP-04 | View upcoming appointments | Must |
| AP-05 | Cancel appointment (configurable cutoff window) | Must |
| AP-06 | Email confirmation via Brevo | Must |
| AP-07 | Reminder email 24h before (EventBridge) | Should |
| AP-08 | Appointment history | Should |
| AP-09 | Attach file/photo (S3 pre-signed URL) | Could |

### 4.4 Admin Dashboard

| # | Requirement | Priority |
|---|---|---|
| AD-01 | Separate admin login | Must |
| AD-02 | View all pending appointments | Must |
| AD-03 | Accept / Decline / Reschedule | Must |
| AD-04 | Send message to user (via Brevo Conversations) | Must |
| AD-05 | Email alert on new appointment (Brevo) | Must |
| AD-06 | User management list | Should |
| AD-07 | Service CRUD | Must |
| AD-08 | Availability calendar | Must |
| AD-09 | Dashboard stats widgets | Should |
| AD-10 | Site config editor (theme, content, language) | Should |
| AD-11 | Export appointments to CSV | Could |

### 4.5 Multi-Language

| # | Requirement |
|---|---|
| I18N-01 | All UI strings in JSON translation files |
| I18N-02 | Language switcher in header |
| I18N-03 | Default + supported languages per site (config) |
| I18N-04 | Initial support: EN, ES |
| I18N-05 | Implementation: `next-intl` |
| I18N-06 | URL-based locale prefix: `/en/`, `/es/` |
| I18N-07 | Email templates in multiple languages (Brevo multi-language templates) |

### 4.6 Theming

| # | Requirement |
|---|---|
| TH-01 | CSS variable-based theme system |
| TH-02 | Light / Dark mode toggle |
| TH-03 | Primary color, accent, font — all in site config |
| TH-04 | Logo + favicon per site |
| TH-05 | Theme applied at build time via site-config.json |

---

## 5. Communication Module

### 5.1 Architecture Overview

```
SiteForge Communication Layer
  │
  ├── Provider: Brevo (primary — all stages)
  │     ├── Transactional emails  (Lambda → Brevo REST API)
  │     ├── Admin inbox           (Brevo Conversations)
  │     ├── Contact sync          (registrations → Brevo contacts)
  │     ├── Email campaigns       (client-managed via Brevo UI)
  │     └── WhatsApp              (future — Brevo WhatsApp API)
  │
  └── Provider: AWS SES (scale migration path)
        └── Transactional only, when volume > 9K emails/month
```

### 5.2 Transactional Email Events

| Event | Recipient | Brevo Template | Trigger |
|---|---|---|---|
| Email verification | User | `siteforge-verify-email` | POST /auth/register |
| Password reset | User | `siteforge-password-reset` | POST /auth/forgot-password |
| Appointment confirmed | User | `siteforge-appt-confirmed` | Admin accepts appointment |
| Appointment declined | User | `siteforge-appt-declined` | Admin declines |
| Appointment rescheduled | User | `siteforge-appt-rescheduled` | Admin reschedules |
| Appointment cancelled | User + Admin | `siteforge-appt-cancelled` | User cancels |
| New appointment alert | Admin | `siteforge-appt-admin-alert` | User books |
| Reminder (24h) | User | `siteforge-appt-reminder` | EventBridge Scheduler |

### 5.3 Lambda Email Helper

```python
# lib/email.py
import boto3
import requests
from functools import lru_cache

class EmailService:
    def __init__(self, site_config: dict):
        self.provider = site_config["email"]["provider"]  # "brevo" or "ses"
        self.sender = site_config["email"]["senderEmail"]
        self.sender_name = site_config["email"]["senderName"]

        if self.provider == "brevo":
            ssm = boto3.client("ssm")
            param = ssm.get_parameter(
                Name=site_config["email"]["apiKeyParam"],
                WithDecryption=True
            )
            self.brevo_api_key = param["Parameter"]["Value"]

    def send(self, template_id: int, to_email: str,
             to_name: str, params: dict) -> bool:
        if self.provider == "brevo":
            return self._send_brevo(template_id, to_email, to_name, params)
        elif self.provider == "ses":
            return self._send_ses(template_id, to_email, to_name, params)

    def _send_brevo(self, template_id, to_email, to_name, params):
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": self.brevo_api_key,
                "Content-Type": "application/json"
            },
            json={
                "to": [{"email": to_email, "name": to_name}],
                "templateId": template_id,
                "params": params,
                "sender": {
                    "email": self.sender,
                    "name": self.sender_name
                }
            }
        )
        return resp.status_code == 201

    def sync_contact(self, email: str, first_name: str,
                     last_name: str, list_id: int):
        """Sync new user registration to Brevo contacts"""
        requests.post(
            "https://api.brevo.com/v3/contacts",
            headers={"api-key": self.brevo_api_key},
            json={
                "email": email,
                "attributes": {
                    "FIRSTNAME": first_name,
                    "LASTNAME": last_name
                },
                "listIds": [list_id],
                "updateEnabled": True
            }
        )
```

### 5.4 Contact Sync Strategy

Every new user registration triggers a Brevo contact sync:
- Stored in a per-site list (e.g. `[site_id]-users`)
- Attributes: first name, last name, phone, registration date, service interest
- This list is the audience for future email campaigns
- No PII beyond what the user provided at registration

### 5.5 Email Campaigns (Client-Managed)

Campaigns are managed by the client directly in the Brevo web UI:

- Audience: the auto-populated `[site_id]-users` list
- Editor: Brevo drag-and-drop (no developer needed)
- Scheduling: client sets date/time in Brevo
- Reporting: open rate, click rate, unsubscribes — all in Brevo

The SiteForge platform does not need to build campaign UI — Brevo provides it.

**Free plan:** 300 emails/day → ~9,000/month  
**Starter plan ($9/mo):** 20,000 emails/month  
**Business plan ($18/mo):** 20,000 + automation workflows

### 5.6 WhatsApp Roadmap

**Phase 1 (Now): Not implemented.** Architecture is ready.

**Phase 2 (Future — 3–6 months):**

| Step | Action |
|---|---|
| 1 | Client creates Meta Business Manager account |
| 2 | Client registers WhatsApp Business number |
| 3 | Connect number to Brevo WhatsApp channel |
| 4 | Create approved message templates in Meta |
| 5 | Enable `whatsapp.enabled: true` in site-config.json |
| 6 | Lambda sends WhatsApp via Brevo API (same SDK) |

**Message templates planned:**

```
Appointment confirmed:
"Hi {{1}}, your {{2}} appointment is confirmed for {{3}} at {{4}}. 
Reply CANCEL to cancel. — {{5}}"

Reminder:
"Hi {{1}}, reminder: {{2}} tomorrow at {{3}}. 
Need to reschedule? Visit {{4}}"
```

**Alternative providers for WhatsApp (if Brevo insufficient):**
- Twilio WhatsApp API — more granular control, better for automation
- Meta Cloud API — free but complex direct integration

### 5.7 Brevo → SES Migration Path

Trigger: client site exceeds ~270 emails/day consistently.

| Step | Action |
|---|---|
| 1 | Submit SES production access request (see Document 1) |
| 2 | Verify sending domain in SES (add DKIM records in Cloudflare) |
| 3 | Update `site-config.json`: `"provider": "ses"` |
| 4 | Deploy update — Lambda email helper auto-switches to boto3 SES |
| 5 | Keep Brevo active for campaigns, inbox, WhatsApp |

```python
# No code change needed — provider flag handles routing:
email_service = EmailService(site_config)
email_service.send(template_id=TMPL_APPT_CONFIRMED, ...)
# → routes to SES or Brevo based on config
```

---

## 6. Data Models (DynamoDB)

### Design: Single-Table per Site

Table name: `{site_id}_main`

```
PK                    SK                    Entity
──────────────────    ─────────────────     ──────────────────
USER#{userId}         PROFILE               User account
USER#{userId}         APPT#{apptId}         Appointment (user index)
APPT#{apptId}         DETAIL                Appointment full record
SERVICE#{serviceId}   DETAIL                Service definition
SLOT#{date}           TIME#{time}           Available time slot
ADMIN#{adminId}       PROFILE               Admin user
CONFIG#SITE           SETTINGS              Site configuration + email config
```

### Key Item Schemas

**User**
```json
{
  "PK": "USER#uuid",
  "SK": "PROFILE",
  "email": "user@example.com",
  "name": "Jane Doe",
  "phone": "+1234567890",
  "passwordHash": "bcrypt-hash",
  "verified": true,
  "lang": "en",
  "createdAt": "2025-01-01T00:00:00Z",
  "GSI1PK": "EMAIL#user@example.com",
  "brevoContactSynced": true
}
```

**Appointment**
```json
{
  "PK": "APPT#uuid",
  "SK": "DETAIL",
  "userId": "uuid",
  "userName": "Jane Doe",
  "userEmail": "user@example.com",
  "serviceId": "uuid",
  "serviceName": "Haircut",
  "date": "2025-07-15",
  "time": "10:00",
  "status": "pending|accepted|declined|rescheduled|cancelled",
  "notes": "First visit",
  "attachmentKey": "uploads/uuid/photo.jpg",
  "adminMessage": "Please arrive 5 min early",
  "reminderSent": false,
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2025-01-01T00:00:00Z",
  "GSI1PK": "STATUS#pending",
  "GSI1SK": "DATE#2025-07-15"
}
```

**Site Config** (includes full communication config)
```json
{
  "PK": "CONFIG#SITE",
  "SK": "SETTINGS",
  "siteName": "My Business",
  "defaultLang": "en",
  "supportedLangs": ["en", "es"],
  "theme": {
    "primaryColor": "#2563eb",
    "accentColor": "#f59e0b",
    "mode": "light",
    "fontFamily": "Fraunces"
  },
  "email": {
    "provider": "brevo",
    "senderName": "My Business",
    "senderEmail": "noreply@mybusiness.com",
    "adminEmail": "admin@mybusiness.com",
    "apiKeyParam": "/siteforge/mybusiness/brevo_api_key",
    "contactListId": 3,
    "templates": {
      "verifyEmail": 1,
      "passwordReset": 2,
      "appointmentConfirmed": 3,
      "appointmentAdminAlert": 4,
      "appointmentReminder": 5,
      "appointmentDeclined": 6,
      "appointmentRescheduled": 7,
      "appointmentCancelled": 8
    }
  },
  "whatsapp": {
    "enabled": false
  },
  "appointments": {
    "windowDays": 30,
    "cancellationHours": 24,
    "reminderHoursBefore": 24
  },
  "modules": ["user-auth", "appointments", "admin-dashboard",
               "notifications", "file-uploads"]
}
```

### GSI (Global Secondary Indexes)

| GSI | PK | SK | Use |
|---|---|---|---|
| GSI1 | GSI1PK | GSI1SK | Admin: query appointments by status + date |
| GSI2 | email (sparse) | — | Auth: login lookup by email |

---

## 7. Infrastructure-as-Code Plan

### Tools: AWS CDK (Python)

**SharedStack** (deployed once per AWS account):
```
SharedStack
  ├── SSM Parameter Store namespace (/siteforge/*)
  └── Reusable IAM managed policies
```

**SiteStack** (deployed per site via `siteforge create`):
```
SiteStack(site_id="mybusiness")
  ├── S3Bucket: mybusiness-frontend (static website)
  ├── S3Bucket: mybusiness-uploads (user files, CORS configured)
  ├── CloudFrontDistribution
  │     ├── Origin 1: S3 frontend (OAI)
  │     └── Origin 2: /api/* → API Gateway
  ├── ACMCertificate (us-east-1, DNS validated via Cloudflare)
  ├── DynamoDBTable: mybusiness_main
  │     ├── GSI1 (status + date queries)
  │     └── GSI2 (email lookup)
  ├── LambdaFunction (Python 3.12, 256MB)
  │     └── IAM Role: DynamoDB RW, S3 RW, SSM read, SES send
  ├── ApiGatewayV2 (HTTP API)
  │     ├── JWT Authorizer (Lambda)
  │     └── Routes → Lambda
  └── EventBridgeRule: appointment-reminders (cron)
```

---

## 8. The SiteForge Installer

### CLI: `siteforge`

```bash
# New site — full provisioning
siteforge create \
  --id mybusiness \
  --domain mybusiness.com \
  --admin admin@mybusiness.com \
  --lang en,es \
  --theme light

# Deploy frontend after config/content changes
siteforge deploy --id mybusiness

# Update a config value
siteforge config --id mybusiness --set theme.primaryColor=#ff6b35

# Add optional module
siteforge add-module --id mybusiness --module payments
siteforge add-module --id mybusiness --module whatsapp

# List all sites
siteforge list

# Destroy site and all AWS resources
siteforge destroy --id mybusiness
```

### Create Flow (Step by Step)

```
siteforge create
  1. Collect: site_id, domain, admin_email, languages, theme
  2. Generate: site-config.json
  3. CDK deploy SiteStack → creates all AWS resources
  4. Build Next.js with site config injected → upload to S3
  5. CloudFront invalidation
  6. Seed DynamoDB: site config + default services
  7. Output Cloudflare DNS instructions:
       CNAME  www  →  [cloudfront-id].cloudfront.net  (DNS only)
       CNAME  @    →  [cloudfront-id].cloudfront.net  (DNS only)
       MX     @    →  inbound.brevo.com (if using Brevo inbox)
  8. Wait for ACM cert validation (DNS record added to Cloudflare)
  9. Print: site URL, admin dashboard URL, first-login credentials
```

### Module System

| Module | Description | Default |
|---|---|---|
| `user-auth` | Registration, JWT, email verify | ✅ |
| `appointments` | Full booking flow | ✅ |
| `admin-dashboard` | Admin panel | ✅ |
| `notifications` | Brevo email integration | ✅ |
| `file-uploads` | S3 pre-signed URL attachments | ✅ |
| `payments` | Stripe checkout | Optional |
| `whatsapp` | Brevo WhatsApp API | Optional |
| `campaigns` | Contact sync to Brevo | Optional |
| `blog` | Markdown posts via S3 | Optional |
| `gallery` | Photo gallery | Optional |
| `analytics` | CloudWatch dashboard embed | Optional |

---

## 9. Implementation Task Breakdown

### Phase 0 — Foundation (Week 1–2) ~36h

| Task | Est |
|---|---|
| Monorepo setup: `apps/frontend`, `apps/api`, `infra/cdk`, `cli` | 4h |
| CDK SharedStack | 3h |
| CDK SiteStack scaffold (all resources) | 8h |
| Python Lambda scaffold: routing, middleware, error handling | 4h |
| Next.js scaffold: layout, routing, theme provider, i18n | 6h |
| DynamoDB single-table helper library (boto3) | 4h |
| siteforge CLI scaffold (Python Typer) | 4h |
| Local dev: SAM + DynamoDB Local | 3h |

### Phase 1 — Auth Module (Week 2–3) ~24h

| Task | Est |
|---|---|
| POST /auth/register + Brevo verify email | 3h |
| GET /auth/verify (token validation) | 2h |
| POST /auth/login → JWT | 2h |
| POST /auth/forgot-password + reset flow | 4h |
| Lambda JWT authorizer | 3h |
| Brevo contact sync on registration | 2h |
| Frontend: Register, Login, Verify, Reset pages | 8h |

### Phase 2 — Appointments Module (Week 3–4) ~28h

| Task | Est |
|---|---|
| GET /services | 2h |
| GET /availability?date= | 3h |
| POST /appointments + Brevo confirmation emails | 4h |
| GET /appointments (user) | 2h |
| DELETE /appointments/{id} + Brevo cancellation emails | 3h |
| EventBridge rule + Lambda for 24h reminders | 3h |
| S3 pre-signed URL for attachments | 2h |
| Frontend: booking flow (service → date → time → confirm) | 8h |
| Frontend: My appointments page | 3h |

### Phase 3 — Admin Dashboard (Week 4–5) ~38h

| Task | Est |
|---|---|
| GET /admin/appointments (filters, pagination) | 3h |
| PATCH /admin/appointments/{id} + status emails | 3h |
| POST /admin/appointments/{id}/message | 2h |
| CRUD /admin/services | 3h |
| CRUD /admin/availability | 3h |
| GET /admin/stats | 2h |
| GET/PATCH /admin/config | 2h |
| Frontend: Admin layout + sidebar | 4h |
| Frontend: Appointments table + action modals | 6h |
| Frontend: Services management | 4h |
| Frontend: Availability calendar | 6h |
| Frontend: Stats widgets | 3h |

### Phase 4 — Landing Page + i18n + Theming (Week 5–6) ~25h

| Task | Est |
|---|---|
| Landing: Hero, Services, About, Contact sections | 10h |
| Extract all strings to EN + ES JSON files | 4h |
| Language switcher component + URL routing | 3h |
| CSS variable theme system + dark/light toggle | 3h |
| Mobile responsive audit | 3h |
| SEO: meta tags, sitemap, robots.txt | 2h |

### Phase 5 — Installer + DevOps (Week 6–7) ~26h

| Task | Est |
|---|---|
| `siteforge create` full flow | 8h |
| `siteforge deploy` (Next.js → S3 + CF invalidation) | 4h |
| `siteforge config` and `add-module` commands | 4h |
| GitHub Actions CI/CD pipeline | 4h |
| CloudWatch alarms (bounce rate, error rate, Lambda errors) | 3h |
| Installer README + client onboarding docs | 3h |

### Phase 6 — QA + Polish (Week 7–8) ~22h

| Task | Est |
|---|---|
| E2E tests: full booking flow (Playwright) | 6h |
| Unit tests: Lambda handlers (pytest + moto) | 4h |
| Security: JWT, CORS, input validation audit | 4h |
| Performance: CloudFront cache tuning | 2h |
| Accessibility audit (WCAG AA) | 3h |
| Mobile testing | 3h |

**Total estimated: ~200h across 8 weeks**

---

## 10. Cost Breakdown

### Per-Site Monthly (< 1,000 users/month)

| Service | Usage | Cost |
|---|---|---|
| CloudFront | 10GB transfer, 1M requests | ~$1.00 |
| S3 frontend | 50MB | ~$0.01 |
| S3 uploads | 1GB | ~$0.02 |
| API Gateway | 100K requests | ~$0.10 |
| Lambda | 100K invocations | ~$0.00 (free tier) |
| DynamoDB | 1M reads, 100K writes | ~$0.25 |
| EventBridge | Reminder rules | ~$0.00 |
| **AWS subtotal** | | **~$1.40/site/mo** |
| Brevo | Free plan | $0.00 |
| Cloudflare DNS | Free | $0.00 |
| Domain (amortized) | $9/yr ÷ 12 | ~$0.75/mo |
| **Total per site** | | **~$2.15/mo** |

### 3-Site Platform Total

| | Cost |
|---|---|
| 3 sites × $2.15 | $6.45 |
| ACM certs | Free |
| **Total/month** | **~$6.45** |

### When to Upgrade Brevo

| Threshold | Action |
|---|---|
| > 300 emails/day | Upgrade to Brevo Starter ($9/mo) |
| > 9,000 emails/month consistently | Migrate transactional to SES ($0.10/1K) |
| > 50K emails/month | SES pays back vs Brevo paid plans |

---

## 11. Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router, static export), TypeScript |
| Styling | Tailwind CSS + CSS variables |
| i18n | next-intl |
| State | Zustand + React Query (TanStack) |
| Backend | Python 3.12, AWS Lambda |
| API | API Gateway v2 (HTTP API) |
| Auth | Custom JWT (PyJWT) + Lambda Authorizer |
| Database | DynamoDB (single-table per site) |
| Files | S3 + pre-signed URLs |
| Email | Brevo REST API (primary) / AWS SES boto3 (scale) |
| Scheduling | EventBridge Scheduler |
| CDN | CloudFront + ACM |
| DNS + Domains | Cloudflare |
| IaC | AWS CDK (Python) |
| CLI | Python + Typer |
| CI/CD | GitHub Actions |
| Local dev | AWS SAM + DynamoDB Local |
| Testing FE | Playwright, Vitest |
| Testing BE | pytest, moto |
| Monorepo | Turborepo |

---

## 12. API Route Reference

```
PUBLIC
  GET  /config                    Site config (theme, langs, content)
  GET  /services                  List active services
  GET  /availability?date=        Available time slots

AUTH
  POST /auth/register             Create account + send verify email
  GET  /auth/verify?token=        Verify email address
  POST /auth/login                Returns JWT
  POST /auth/logout               Clears cookie
  POST /auth/forgot-password      Send reset email
  POST /auth/reset-password       Set new password

USER (JWT required)
  GET    /me                      Get profile
  PATCH  /me                      Update profile
  GET    /appointments            List my appointments
  POST   /appointments            Book appointment
  DELETE /appointments/{id}       Cancel appointment

ADMIN (Admin JWT required)
  GET    /admin/appointments               All appointments + filters
  PATCH  /admin/appointments/{id}          Update status
  POST   /admin/appointments/{id}/message  Message to user
  GET    /admin/users                      User list
  GET    /admin/stats                      Dashboard metrics
  GET    /admin/services                   List services
  POST   /admin/services                   Create service
  PATCH  /admin/services/{id}              Update service
  DELETE /admin/services/{id}              Deactivate service
  GET    /admin/availability               Get open slots
  POST   /admin/availability               Add slots
  DELETE /admin/availability/{id}          Remove slot
  GET    /admin/config                     Get site config
  PATCH  /admin/config                     Update site config
```

---

*Document version 1.1 — Cloudflare + Brevo edition*  
*Previous version: 1.0 (Route 53 + SES-only)*
