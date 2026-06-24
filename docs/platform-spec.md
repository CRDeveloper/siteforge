# SiteForge Platform — Requirements, Architecture & Implementation Spec

> A self-hosted, AWS-native website platform with appointment booking, admin dashboard, multi-language, theming, and a WordPress-style site installer — all under $10/month.

---

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Hosting Comparison](#2-hosting-comparison)
3. [System Architecture](#3-system-architecture)
4. [Feature Requirements](#4-feature-requirements)
5. [Data Models (DynamoDB)](#5-data-models-dynamodb)
6. [Infrastructure-as-Code Plan](#6-infrastructure-as-code-plan)
7. [The Site Package Installer](#7-the-site-package-installer)
8. [Implementation Task Breakdown](#8-implementation-task-breakdown)
9. [Cost Breakdown](#9-cost-breakdown)
10. [Tech Stack Summary](#10-tech-stack-summary)

---

## 1. Project Vision

Build a **reusable, installable website platform** that:

- Hosts multiple independent websites on shared AWS infrastructure
- Each site has: landing page + user portal + admin dashboard
- Core use case: service businesses accepting appointments online
- New sites deploy via a CLI/script installer (like `wp-config.php` but for AWS)
- Budget target: **< $10/month total** across all hosted sites

### Core Principles

| Principle | Decision |
|---|---|
| Serverless-first | Lambda + API Gateway (no EC2) |
| Static where possible | Next.js static export on S3 + CloudFront |
| One DynamoDB table per site | Isolated data, predictable costs |
| Config-driven | Each site is a JSON config, not a codebase fork |
| Open extension model | "Plugins" are Lambda-backed feature modules |

---

## 2. Hosting Comparison

### Option A: AWS (CloudFront + S3 + Lambda) ← Recommended

| Layer | Service | Cost |
|---|---|---|
| Frontend | S3 + CloudFront | ~$0.50–$2/mo |
| Backend API | API Gateway + Lambda | ~$0–$1/mo (free tier) |
| Database | DynamoDB on-demand | ~$0–$1/mo |
| Email | SES | ~$0.10/1000 emails |
| Storage | S3 (uploads) | ~$0.023/GB |
| Domain | Route 53 | $0.50/mo/hosted zone |
| SSL | ACM | Free |
| **Total (2–3 sites)** | | **$3–$8/mo** |

**Pros:** Infinite scale, no server mgmt, AWS ecosystem, CloudFront CDN global, pay-per-use  
**Cons:** Cold starts on Lambda, AWS complexity, IAM learning curve

---

### Option B: Vercel/Netlify + PlanetScale/Supabase

| Layer | Service | Cost |
|---|---|---|
| Frontend + API | Vercel (Hobby) | Free / $20 Pro |
| Database | PlanetScale Hobby | Free (limited) |
| Email | Resend | Free tier |
| **Total** | | **$0–$20/mo** |

**Pros:** Zero DevOps, excellent DX, instant deploys  
**Cons:** Free tier limits hit quickly, no DynamoDB, vendor lock-in, not AWS-native, exit costs

---

### Option C: cPanel Shared Hosting

| Layer | Service | Cost |
|---|---|---|
| Hosting | Shared cPanel host | $3–$8/mo |
| DB | MySQL included | — |
| Email | cPanel email | — |
| CDN | Cloudflare free | Free |
| **Total** | | **$3–$8/mo** |

**Pros:** Familiar, cheap, PHP/WordPress friendly  
**Cons:** Not serverless, PHP-only backend, no Lambda/DynamoDB, poor for Next.js, scaling requires upgrade, not programmable infrastructure

---

### Recommendation Matrix

| Need | Best Choice |
|---|---|
| Full AWS ecosystem | **Option A** |
| Fastest MVP | Option B |
| Non-technical team | Option C |
| Multi-site platform under $10 | **Option A** |
| Custom Python backend | **Option A** |

**→ Go with Option A (CloudFront + S3 + Lambda).** It matches your stack requirements and scales to multiple sites without per-site cost increases.

---

### Domain Registration: CloudFront vs Route 53

- **Register domains in Route 53** — not "in CloudFront." CloudFront is the CDN distribution, Route 53 is DNS.
- Route 53 domain registration: $9–$14/year for `.com`
- Each site needs a hosted zone ($0.50/mo) + CloudFront distribution (free, pay for data transfer)
- SSL via ACM (free) attached to each CloudFront distribution

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   SHARED INFRASTRUCTURE              │
│                                                      │
│  Route 53 (DNS)   ACM (SSL Certs)   SES (Email)     │
│  S3 Uploads Bucket   DynamoDB (per-site tables)      │
└─────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│  SITE A      │    │  SITE B          │   ... N sites
│              │    │                  │
│ CloudFront   │    │  CloudFront      │
│     │        │    │      │           │
│     ▼        │    │      ▼           │
│  S3 Bucket   │    │   S3 Bucket      │
│ (Next.js     │    │  (Next.js        │
│  static)     │    │   static)        │
│     │        │    │      │           │
│     ▼        │    │      ▼           │
│ API Gateway  │    │  API Gateway     │
│     │        │    │      │           │
│     ▼        │    │      ▼           │
│  Lambda      │    │   Lambda         │
│ (Python)     │    │  (Python)        │
│     │        │    │      │           │
│     ▼        │    │      ▼           │
│  DynamoDB    │    │   DynamoDB       │
│  Table(s)    │    │   Table(s)       │
└──────────────┘    └──────────────────┘

Site Installer CLI
  → Runs CloudFormation/CDK
  → Creates all resources for a new site
  → Deploys config JSON
  → Sets up DNS + SSL
```

---

### Request Flow — User Books Appointment

```
User Browser
  → CloudFront (CDN, SSL termination)
  → S3 (Next.js static page served)
  → [User submits form]
  → API Gateway POST /appointments
  → Lambda (Python) handler
      → Validates input
      → Writes to DynamoDB
      → Sends SES email to admin
      → Returns 200 OK
  → Next.js shows confirmation
  → Admin sees it in dashboard (polling or WebSocket)
```

---

## 4. Feature Requirements

### 4.1 Public Landing Page

| # | Requirement | Priority |
|---|---|---|
| LP-01 | Hero section with CTA (Book Now / Register) | Must |
| LP-02 | Services section (configurable per site) | Must |
| LP-03 | About / Team section | Should |
| LP-04 | Contact info + map embed | Should |
| LP-05 | Multi-language toggle (i18n) | Must |
| LP-06 | Theme support (light/dark + color scheme) | Must |
| LP-07 | Mobile responsive (320px–2560px) | Must |
| LP-08 | SEO meta tags (configurable) | Must |
| LP-09 | Cookie consent banner | Should |
| LP-10 | Social media links | Could |

### 4.2 User Registration & Auth

| # | Requirement | Priority |
|---|---|---|
| AU-01 | Register with email + password | Must |
| AU-02 | Email verification on signup | Must |
| AU-03 | Login / Logout | Must |
| AU-04 | Password reset via email | Must |
| AU-05 | JWT-based sessions (stored in httpOnly cookie) | Must |
| AU-06 | Social login (Google) | Could |
| AU-07 | User profile page (name, phone, photo) | Should |

### 4.3 Appointment Booking (User)

| # | Requirement | Priority |
|---|---|---|
| AP-01 | Browse available services | Must |
| AP-02 | Select date/time from available slots | Must |
| AP-03 | Submit appointment request | Must |
| AP-04 | View upcoming appointments | Must |
| AP-05 | Cancel appointment (with configurable window) | Must |
| AP-06 | Receive email confirmation | Must |
| AP-07 | Receive reminder email (24h before) | Should |
| AP-08 | View appointment history | Should |
| AP-09 | Attach file/photo to appointment (S3) | Could |

### 4.4 Admin Dashboard

| # | Requirement | Priority |
|---|---|---|
| AD-01 | Login with separate admin credentials | Must |
| AD-02 | View all pending appointments | Must |
| AD-03 | Accept / Decline / Reschedule appointments | Must |
| AD-04 | Send message to user about appointment | Must |
| AD-05 | Email notification on new appointment | Must |
| AD-06 | User management list | Should |
| AD-07 | Service management (add/edit/remove services) | Must |
| AD-08 | Availability calendar (set open time slots) | Must |
| AD-09 | Dashboard stats (total bookings, this week, etc.) | Should |
| AD-10 | Site config editor (theme, language, content) | Should |
| AD-11 | Export appointments to CSV | Could |

### 4.5 Multi-Language (i18n)

| # | Requirement |
|---|---|
| I18N-01 | All UI strings in JSON translation files |
| I18N-02 | Language switcher in header |
| I18N-03 | Default language per site (config) |
| I18N-04 | Supported: EN, ES + others via config |
| I18N-05 | Next.js `next-intl` or `react-i18next` |
| I18N-06 | URL-based locale (`/en/`, `/es/`) or cookie-based |

### 4.6 Theming

| # | Requirement |
|---|---|
| TH-01 | CSS variable-based theme system |
| TH-02 | Light / Dark mode toggle |
| TH-03 | Primary color, accent color, font — all configurable |
| TH-04 | Theme config loaded from site JSON at build/runtime |
| TH-05 | Logo and favicon per site |

---

## 5. Data Models (DynamoDB)

### Design: Single-Table per Site

Each site gets its own DynamoDB table: `{site_id}_main`

Using single-table design with composite keys:

```
PK (Partition Key)    SK (Sort Key)         Entity
──────────────────    ─────────────         ──────
USER#{userId}         PROFILE               User record
USER#{userId}         APPT#{apptId}         User's appointment
APPT#{apptId}         DETAIL                Appointment detail
SERVICE#{serviceId}   DETAIL                Service definition
SLOT#{date}           TIME#{time}           Available time slot
ADMIN#{adminId}       PROFILE               Admin user
CONFIG#SITE           SETTINGS              Site configuration
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
  "passwordHash": "...",
  "verified": true,
  "createdAt": "ISO8601",
  "GSI1PK": "EMAIL#user@example.com"
}
```

**Appointment**
```json
{
  "PK": "APPT#uuid",
  "SK": "DETAIL",
  "userId": "uuid",
  "serviceId": "uuid",
  "date": "2025-07-15",
  "time": "10:00",
  "status": "pending | accepted | declined | rescheduled | cancelled",
  "notes": "...",
  "attachmentKey": "s3-key",
  "adminMessage": "...",
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601",
  "GSI1PK": "STATUS#pending",
  "GSI1SK": "DATE#2025-07-15"
}
```

**Service**
```json
{
  "PK": "SERVICE#uuid",
  "SK": "DETAIL",
  "name": {"en": "Haircut", "es": "Corte de pelo"},
  "description": {"en": "...", "es": "..."},
  "durationMinutes": 60,
  "active": true
}
```

**Site Config**
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
    "fontFamily": "Inter"
  },
  "adminEmail": "admin@business.com",
  "appointmentWindowDays": 30,
  "cancellationHours": 24
}
```

### GSI (Global Secondary Indexes)

| GSI | PK | SK | Purpose |
|---|---|---|---|
| GSI1 | GSI1PK | GSI1SK | Query by status/date (admin view) |
| GSI2 | email | — | Login lookup by email |

---

## 6. Infrastructure-as-Code Plan

### Tools: AWS CDK (Python) + CloudFormation

Each site deploy creates a **CDK Stack**:

```
SiteStack(site_id="mybusiness")
  ├── S3Bucket (frontend static)
  ├── CloudFrontDistribution
  │     └── OAI → S3
  │     └── /api/* → API Gateway
  ├── ACMCertificate (us-east-1)
  ├── Route53ARecord → CloudFront
  ├── DynamoDBTable (mybusiness_main)
  │     └── GSI1, GSI2
  ├── S3Bucket (uploads)
  │     └── CORS config
  ├── LambdaFunction (Python 3.12)
  │     └── IAM Role (DynamoDB, S3, SES)
  ├── ApiGateway (REST)
  │     └── Routes → Lambda
  └── SESIdentity (admin email)
```

### Shared Stack (deployed once)

```
SharedStack
  ├── SES domain verification
  ├── IAM policies (reusable)
  └── SSM Parameter Store (shared secrets)
```

---

## 7. The Site Package Installer

**Concept:** Like WordPress's famous 5-minute install, but for AWS.

### CLI Tool: `siteforge`

```bash
# Install new site
siteforge create --id mybusiness --domain mybusiness.com --admin admin@mybusiness.com

# Update site config
siteforge config --id mybusiness --set theme.primaryColor=#ff0000

# Deploy frontend
siteforge deploy --id mybusiness

# Add a feature module (plugin equivalent)
siteforge add-module --id mybusiness --module payments

# List all sites
siteforge list

# Destroy a site
siteforge destroy --id mybusiness
```

### Installer Flow

```
1. siteforge create
   ├── Prompt: site_id, domain, admin_email, language, theme
   ├── Generate: site-config.json
   ├── Run: cdk deploy SiteStack-{site_id}
   │     └── Creates all AWS resources
   ├── Deploy: Next.js frontend to S3
   ├── Seed: DynamoDB with site config + default services
   ├── Verify: SES email identity
   └── Output: Site URL, admin login URL, credentials
```

### site-config.json (per site)

```json
{
  "siteId": "mybusiness",
  "domain": "mybusiness.com",
  "siteName": "My Business",
  "adminEmail": "admin@mybusiness.com",
  "defaultLang": "en",
  "supportedLangs": ["en", "es"],
  "theme": {
    "primaryColor": "#2563eb",
    "mode": "light",
    "font": "Inter"
  },
  "modules": ["appointments", "user-auth", "admin-dashboard"],
  "content": {
    "hero": {
      "en": { "title": "Welcome", "subtitle": "Book your appointment" },
      "es": { "title": "Bienvenido", "subtitle": "Reserva tu cita" }
    },
    "services": []
  }
}
```

### Module System (Plugin Equivalent)

| Module | Description | Default |
|---|---|---|
| `user-auth` | Registration, login, JWT | ✓ |
| `appointments` | Full booking system | ✓ |
| `admin-dashboard` | Admin panel | ✓ |
| `notifications` | Email via SES | ✓ |
| `file-uploads` | S3 attachments | ✓ |
| `payments` | Stripe integration | Optional |
| `chat` | Admin↔user messaging | Optional |
| `analytics` | CloudWatch dashboard | Optional |
| `blog` | Markdown blog posts | Optional |
| `gallery` | Photo gallery (S3) | Optional |

---

## 8. Implementation Task Breakdown

### Phase 0 — Foundation (Week 1–2)

| Task | Owner | Est |
|---|---|---|
| P0-01 | Monorepo setup (turborepo or nx): `apps/frontend`, `apps/api`, `infra/cdk`, `cli` | Backend | 4h |
| P0-02 | CDK SharedStack (SES verification, base IAM) | DevOps | 3h |
| P0-03 | CDK SiteStack scaffold (S3, CloudFront, DynamoDB, Lambda, APIGW) | DevOps | 8h |
| P0-04 | Python Lambda scaffold: routing, middleware, error handling | Backend | 4h |
| P0-05 | Next.js app scaffold: layout, routing, i18n setup, theme provider | Frontend | 6h |
| P0-06 | DynamoDB table design + helper library (boto3 wrapper) | Backend | 4h |
| P0-07 | siteforge CLI scaffold (Python Click or Typer) | DevOps | 4h |
| P0-08 | Local dev environment (LocalStack or SAM) | DevOps | 3h |

### Phase 1 — Auth & User Module (Week 2–3)

| Task | Owner | Est |
|---|---|---|
| A-01 | POST /auth/register — create user, send verify email | Backend | 3h |
| A-02 | GET /auth/verify?token= — verify email | Backend | 2h |
| A-03 | POST /auth/login — return JWT | Backend | 2h |
| A-04 | POST /auth/forgot-password — send reset email | Backend | 2h |
| A-05 | POST /auth/reset-password — set new password | Backend | 2h |
| A-06 | JWT middleware (Lambda authorizer) | Backend | 3h |
| A-07 | Frontend: Register page | Frontend | 4h |
| A-08 | Frontend: Login page | Frontend | 3h |
| A-09 | Frontend: Email verification flow | Frontend | 2h |
| A-10 | Frontend: Password reset flow | Frontend | 3h |
| A-11 | Frontend: User profile page | Frontend | 3h |

### Phase 2 — Appointments Module (Week 3–4)

| Task | Owner | Est |
|---|---|---|
| AP-01 | GET /services — list active services | Backend | 2h |
| AP-02 | GET /availability?date= — available slots | Backend | 3h |
| AP-03 | POST /appointments — create appointment | Backend | 3h |
| AP-04 | GET /appointments (user) — list user's appointments | Backend | 2h |
| AP-05 | DELETE /appointments/{id} — cancel | Backend | 2h |
| AP-06 | SES email: new booking confirmation to user | Backend | 2h |
| AP-07 | SES email: new booking notification to admin | Backend | 1h |
| AP-08 | SES email: reminder scheduler (EventBridge rule) | Backend | 3h |
| AP-09 | Frontend: Book appointment flow (service → date → time → confirm) | Frontend | 8h |
| AP-10 | Frontend: My appointments page | Frontend | 4h |
| AP-11 | S3 pre-signed URL for file attachment | Backend | 2h |

### Phase 3 — Admin Dashboard (Week 4–5)

| Task | Owner | Est |
|---|---|---|
| AD-01 | GET /admin/appointments — all with filters | Backend | 3h |
| AD-02 | PATCH /admin/appointments/{id} — accept/decline/reschedule | Backend | 3h |
| AD-03 | POST /admin/appointments/{id}/message — send msg to user | Backend | 2h |
| AD-04 | GET/POST/PATCH /admin/services — CRUD services | Backend | 3h |
| AD-05 | GET/POST /admin/availability — manage open slots | Backend | 3h |
| AD-06 | GET /admin/users — list users | Backend | 2h |
| AD-07 | GET /admin/stats — dashboard metrics | Backend | 2h |
| AD-08 | Frontend: Admin layout + sidebar nav | Frontend | 4h |
| AD-09 | Frontend: Appointments table (filter, sort, action buttons) | Frontend | 6h |
| AD-10 | Frontend: Accept/Decline/Reschedule modal | Frontend | 4h |
| AD-11 | Frontend: Services management page | Frontend | 4h |
| AD-12 | Frontend: Availability calendar | Frontend | 6h |
| AD-13 | Frontend: Dashboard stats widgets | Frontend | 3h |
| AD-14 | Frontend: User list page | Frontend | 3h |

### Phase 4 — Landing Page & Content (Week 5–6)

| Task | Owner | Est |
|---|---|---|
| LP-01 | Landing page: Hero, CTA | Frontend | 4h |
| LP-02 | Landing page: Services section (data from API) | Frontend | 3h |
| LP-03 | Landing page: About/Contact sections | Frontend | 3h |
| LP-04 | i18n: Extract all strings, create EN + ES JSON | Frontend | 4h |
| LP-05 | Language switcher component | Frontend | 2h |
| LP-06 | Theme provider: CSS variables, dark/light toggle | Frontend | 3h |
| LP-07 | Mobile responsive audit + fixes | Frontend | 4h |
| LP-08 | SEO: meta tags, sitemap, robots.txt | Frontend | 2h |

### Phase 5 — Installer & DevOps (Week 6–7)

| Task | Owner | Est |
|---|---|---|
| IN-01 | siteforge create command (full flow) | DevOps | 8h |
| IN-02 | siteforge deploy command (Next.js → S3 + CloudFront invalidation) | DevOps | 4h |
| IN-03 | siteforge config command | DevOps | 3h |
| IN-04 | siteforge add-module command | DevOps | 4h |
| IN-05 | CI/CD pipeline (GitHub Actions): build → deploy per site | DevOps | 4h |
| IN-06 | CloudWatch alarms + basic monitoring | DevOps | 2h |
| IN-07 | Installer documentation (README + walkthrough) | All | 3h |

### Phase 6 — Polish & Testing (Week 7–8)

| Task | Owner | Est |
|---|---|---|
| QA-01 | E2E tests: full booking flow (Playwright) | QA | 6h |
| QA-02 | Unit tests: Lambda handlers (pytest) | Backend | 4h |
| QA-03 | Mobile testing across devices | Frontend | 3h |
| QA-04 | Security audit: JWT, CORS, input validation | Backend | 4h |
| QA-05 | Performance: CloudFront cache tuning, Lambda cold start | DevOps | 3h |
| QA-06 | Accessibility audit (WCAG AA) | Frontend | 3h |
| QA-07 | Load test with >100 concurrent users | DevOps | 2h |

---

## 9. Cost Breakdown

### Per-Site Monthly Cost (at low traffic, <1000 users/month)

| Service | Usage | Cost |
|---|---|---|
| CloudFront | 10GB transfer, 1M requests | ~$1.00 |
| S3 (frontend) | 50MB storage | ~$0.01 |
| S3 (uploads) | 1GB storage | ~$0.02 |
| API Gateway | 100K requests | ~$0.10 |
| Lambda | 100K invocations, 256MB | ~$0.00 (free tier) |
| DynamoDB | 1M reads, 100K writes | ~$0.25 |
| SES | 1000 emails | ~$0.10 |
| Route 53 | 1 hosted zone | ~$0.50 |
| EventBridge | Reminder rules | ~$0.00 |
| **Per-site total** | | **~$2.00/mo** |

### Multi-Site Platform (3 sites)

| | Cost |
|---|---|
| 3 sites × $2 | $6.00 |
| Shared SES domain | $0.50 |
| ACM certs | Free |
| **Total** | **~$6.50/mo** |

### Domain Costs (one-time/annual)

| | Cost |
|---|---|
| .com registration (Route 53) | $13/year |
| Hosted zone | $0.50/mo = $6/year |
| **Per domain/year** | **~$19/year** |

---

## 10. Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend framework | Next.js 14 (App Router, static export) |
| Frontend language | TypeScript |
| Styling | Tailwind CSS + CSS variables |
| i18n | next-intl |
| State management | Zustand + React Query |
| Backend language | Python 3.12 |
| Backend framework | AWS Lambda + Mangum (ASGI adapter) or plain handlers |
| API style | REST (API Gateway v2 HTTP API) |
| Auth | Custom JWT (PyJWT) + Lambda Authorizer |
| Database | DynamoDB (single-table per site) |
| File storage | S3 (pre-signed URLs) |
| Email | AWS SES |
| Scheduling | EventBridge Scheduler (reminders) |
| CDN | CloudFront |
| DNS | Route 53 |
| SSL | ACM |
| IaC | AWS CDK (Python) |
| CLI | Python + Typer |
| CI/CD | GitHub Actions |
| Local dev | AWS SAM or LocalStack |
| Testing (FE) | Playwright, Vitest |
| Testing (BE) | pytest, moto (DynamoDB mock) |
| Monorepo | Turborepo |

---

## Appendix: API Route Reference

```
PUBLIC
  GET    /config              ← Site config (theme, langs, content)
  GET    /services            ← List services
  GET    /availability        ← Available slots by date

AUTH
  POST   /auth/register
  GET    /auth/verify
  POST   /auth/login
  POST   /auth/logout
  POST   /auth/forgot-password
  POST   /auth/reset-password

USER (JWT required)
  GET    /me                  ← Profile
  PATCH  /me                  ← Update profile
  GET    /appointments        ← My appointments
  POST   /appointments        ← Book appointment
  DELETE /appointments/{id}   ← Cancel
  GET    /appointments/{id}/messages

ADMIN (Admin JWT required)
  GET    /admin/appointments
  PATCH  /admin/appointments/{id}
  POST   /admin/appointments/{id}/message
  GET    /admin/users
  GET    /admin/stats
  GET    /admin/services
  POST   /admin/services
  PATCH  /admin/services/{id}
  DELETE /admin/services/{id}
  GET    /admin/availability
  POST   /admin/availability
  DELETE /admin/availability/{id}
  GET    /admin/config
  PATCH  /admin/config
```

---

*Document version 1.0 — Ready for sprint planning*
