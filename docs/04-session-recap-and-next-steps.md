# SiteForge — Session Recap & Handoff
*Generated: June 2026 · Ready for IDE import*

---

## What We Built

A full **AWS-native multi-site appointment booking platform** from scratch — architecture, documentation, infrastructure code, backend API, and complete frontend. The platform works like a self-hosted WordPress for service businesses, but built on Python Lambda + Next.js + DynamoDB with a CLI installer.

---

## Documents Produced (download separately)

| File | Contents |
|---|---|
| `01-ses-production-access-request.md` | Copy-paste AWS SES sandbox removal form with bounce handling, anti-spam compliance, and Cloudflare DNS records |
| `02-brevo-setup-guide.md` | Step-by-step Brevo onboarding for each client — domain verify, DNS, API key, 8 email templates, Conversations inbox, campaigns, WhatsApp roadmap, client handoff checklist |
| `03-platform-spec-v1.1.md` | Full platform spec: architecture, feature requirements, DynamoDB models, CDK plan, module system, API routes, cost breakdown |
| `siteforge-monorepo.zip` | Complete monorepo — 63 files, ready to `git init` and push |

---

## Key Decisions Made

| Topic | Decision | Reason |
|---|---|---|
| DNS & Domains | **Cloudflare** (not Route 53) | At-cost domains (~$9/yr), free DNS, free DDoS — saves ~$13/site/yr vs Route 53 |
| Email | **Brevo** as primary platform | Transactional + admin inbox + campaigns + WhatsApp in one — replaces cPanel's built-in MTA |
| Email at scale | **AWS SES** migration path | Switch via config flag when > 9K emails/month; Brevo stays for campaigns/WhatsApp |
| Backend | **Python 3.12 Lambda** | Team skill, no cold-start issue at this scale, CDK v2 native |
| Frontend | **Next.js 14 static export → S3** | Zero server cost, CloudFront CDN, pennies/month |
| Database | **DynamoDB single-table per site** | Isolated data, on-demand pricing, ~$0.25/mo at low traffic |
| Infrastructure | **AWS CDK v2 (Python)** | Team knows AWS, programmatic, version-controlled |
| Multi-site | **Config-driven** — `site-config.json` per site | No code forks, one installer creates everything |
| Theming | **CSS variables** injected at runtime from config | Full rebrand per site, no rebuild needed |
| i18n | **next-intl** with JSON files | EN + ES default, any language addable via JSON |
| Auth | **Custom JWT** (PyJWT) + httpOnly cookie | No Cognito cost/complexity, fits Lambda authorizer pattern |
| CI/CD | **GitHub Actions** — detects changed sites | Only redeploys sites whose code/config actually changed |

---

## Monorepo Structure

```
siteforge/
├── apps/
│   ├── api/                        ✅ COMPLETE
│   │   ├── main.py                 Router — method+path → handler
│   │   ├── middleware/
│   │   │   ├── auth.py             JWT extract, decode, inject into request
│   │   │   └── cors.py             CORS preflight response
│   │   ├── handlers/
│   │   │   ├── auth/__init__.py    register, login, logout, verify, forgot/reset password
│   │   │   ├── appointments/       list, create (+ emails), cancel (+ slot release)
│   │   │   ├── admin/__init__.py   appointments CRUD, users, stats, services, availability, config
│   │   │   ├── public/__init__.py  /config, /services, /availability
│   │   │   ├── me.py               GET/PATCH user profile
│   │   │   ├── scheduler.py        EventBridge → 24h reminder emails
│   │   │   └── uploads.py          S3 pre-signed URL generator
│   │   └── lib/
│   │       ├── db.py               DynamoDB single-table helpers (get, put, query, update, scan)
│   │       ├── email.py            Brevo + SES dual provider, contact sync
│   │       └── response.py         ok(), error(), created(), set_cookie(), clear_cookie()
│   │
│   └── frontend/                   ✅ COMPLETE
│       ├── next.config.js          Static export, site-config injected at build via SITE_ID env
│       ├── tailwind.config.js      CSS variable-based theme tokens
│       ├── tsconfig.json
│       ├── postcss.config.js
│       └── src/
│           ├── app/
│           │   ├── layout.tsx      Root — fonts, ThemeProvider, Providers (React Query), next-intl
│           │   ├── (public)/
│           │   │   ├── page.tsx    Landing page — Hero, Services, About, Contact
│           │   │   └── book/       3-step booking wizard (service → date/time → confirm → success)
│           │   ├── (auth)/
│           │   │   ├── layout.tsx  Minimal centered auth layout
│           │   │   └── auth/
│           │   │       ├── login/
│           │   │       ├── register/
│           │   │       ├── forgot-password/
│           │   │       └── reset-password/
│           │   ├── (user)/
│           │   │   ├── layout.tsx          Auth guard → redirects to login
│           │   │   └── appointments/       List upcoming/past, cancel with modal
│           │   └── (admin)/
│           │       └── admin/
│           │           ├── layout.tsx      Sidebar nav + mobile drawer, admin guard
│           │           ├── page.tsx        Dashboard — stat cards + pending queue
│           │           ├── appointments/   Table with accept/decline/reschedule/message modals
│           │           ├── services/       Service CRUD with bilingual form modal
│           │           └── users/          User list table
│           ├── components/
│           │   ├── layout/
│           │   │   ├── Header.tsx      Sticky nav, lang switcher, dark mode toggle, mobile menu
│           │   │   ├── Footer.tsx
│           │   │   └── ThemeProvider.tsx  CSS variable injection from site-config theme
│           │   └── ui/
│           │       ├── Button.tsx
│           │       ├── ServiceCard.tsx
│           │       └── index.tsx       Input, Textarea, FormField, Alert, Badge, Modal, Spinner
│           ├── i18n/
│           │   ├── request.ts
│           │   └── locales/
│           │       ├── en/common.json  ~80 English strings
│           │       └── es/common.json  ~80 Spanish strings
│           ├── lib/
│           │   ├── api.ts          Full typed API client + all TypeScript interfaces
│           │   ├── store.ts        Zustand auth store with persist
│           │   └── providers.tsx   React Query client wrapper
│           └── styles/
│               └── globals.css     CSS variables, Tailwind base, .btn/.card/.input classes
│
├── infra/
│   └── cdk/                        ✅ COMPLETE
│       ├── app.py                  Reads sites/* → one SiteStack per site
│       ├── cdk.json
│       ├── requirements.txt
│       └── stacks/
│           ├── shared_stack.py     IAM managed policy, SSM namespace
│           └── site_stack.py       S3×2, CloudFront, ACM, DynamoDB+GSI×2,
│                                   Lambda, API Gateway v2, EventBridge, SSM param
│
├── cli/
│   └── siteforge/                  🟡 PARTIAL (4/7 commands done)
│       ├── __main__.py
│       └── commands/
│           ├── create.py           ✅ Full provision → SSM → CDK → next-steps output
│           ├── deploy.py           ✅ Build → S3 sync → CloudFront invalidation
│           ├── config.py           ✅ Dot-path read/write on site-config.json
│           ├── list_sites.py       ✅ Rich table of all sites
│           ├── seed.py             ❌ TODO
│           ├── destroy.py          ❌ TODO
│           └── add_module.py       ❌ TODO
│
├── sites/
│   └── serenity-therapy/           ✅ SAMPLE CLIENT
│       └── site-config.json        Sage green theme, EN+ES, 4 therapy services
│
├── .github/workflows/deploy.yml    ✅ Matrix deploy, change detection
├── .gitignore                      ✅
├── package.json                    ✅ Turborepo workspaces
├── turbo.json                      ✅ build → test → deploy pipeline
└── README.md                       ✅ Full setup guide
```

---

## What Is NOT Yet Done

### 🔴 Priority 1 — Finish core platform

**Frontend pages missing:**

| Page | Route | Notes |
|---|---|---|
| Email verify | `/auth/verify` | Calls GET /auth/verify on load, shows success/error, redirects to login |
| Availability calendar | `/admin/availability` | Week view, click dates to add time slots, calls POST/DELETE /admin/availability |
| Site settings | `/admin/settings` | Live theme color picker, font selector, dark/light toggle, hero/about content editor |
| User profile | `/user/profile` | Edit name, phone, preferred language |
| Error boundary | `app/error.tsx` | Global Next.js error boundary |
| 404 page | `app/not-found.tsx` | Branded 404 |

**CLI commands missing:**

| Command | What it does |
|---|---|
| `siteforge seed --id X` | Creates admin user in DynamoDB, seeds services from site-config, adds default availability slots for next 30 days |
| `siteforge destroy --id X` | Confirm prompt → CDK destroy → SSM param cleanup |
| `siteforge add-module --id X --module Y` | Appends module to site-config.json, deploys relevant Lambda function additions |

**API tests missing:**

| File | Coverage |
|---|---|
| `apps/api/tests/conftest.py` | moto DynamoDB fixtures, fake SSM, test client |
| `apps/api/tests/test_auth.py` | register, login, verify, reset flows |
| `apps/api/tests/test_appointments.py` | create, list, cancel, double-booking guard |
| `apps/api/tests/test_admin.py` | accept, decline, reschedule, stats, services CRUD |

### 🟡 Priority 2 — Production polish

- SEO: `generateMetadata()` in landing page from site-config seo fields
- `public/robots.txt` and `sitemap.xml` at build time
- `packages/shared-types/src/index.ts` — deduplicate TypeScript interfaces from `api.ts`
- Admin availability page needs a proper week-view calendar component
- Bounce/complaint SNS handler Lambda stub (referenced in SES access request)
- Local dev setup: SAM template or LocalStack config for offline Lambda + DynamoDB

### 🟢 Priority 3 — Optional modules (post-launch)

| Module | Effort |
|---|---|
| `payments` | Stripe Lambda handler + `/book/payment` step |
| `whatsapp` | Brevo WhatsApp API, Meta Business approval flow |
| `blog` | Markdown in S3, SSG at build, admin upload |
| `gallery` | S3 photo gallery, pre-signed upload in admin |
| `analytics` | CloudWatch embeds or Plausible |

---

## IDE Setup — Step by Step

### 1. Unzip and init git

```bash
unzip siteforge-monorepo.zip
cd siteforge
git init
git add .
git commit -m "feat: initial SiteForge platform scaffold"
```

### 2. Push to GitHub

```bash
# Create empty repo on GitHub first (no README)
git remote add origin git@github.com:YOUR_ORG/siteforge.git
git branch -M main
git push -u origin main
```

### 3. Install dependencies

```bash
# Node (turborepo + frontend)
npm install

# Python — CDK infra
cd infra/cdk && pip install -r requirements.txt && cd ../..

# Python — API local dev + tests
cd apps/api && pip install -r requirements.txt && pip install pytest moto && cd ../..

# Python — CLI
pip install typer rich boto3
```

### 4. Add GitHub Secrets

GitHub → repo → Settings → Secrets and variables → Actions:

```
AWS_ACCESS_KEY_ID        IAM user with CDK + S3 + CloudFront + DynamoDB access
AWS_SECRET_ACCESS_KEY    IAM user secret
AWS_ACCOUNT_ID           12-digit AWS account number
```

### 5. Bootstrap CDK (once per account/region)

```bash
cd infra/cdk
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

### 6. Deploy shared stack

```bash
cdk deploy SiteForgeShared
```

### 7. Create serenity-therapy site

```bash
python -m cli.siteforge create \
  --id serenity-therapy \
  --domain serenity-therapy.com \
  --admin admin@serenity-therapy.com \
  --name "Serenity Therapy" \
  --color "#5c7a6e"
```

### 8. Add secrets to SSM

```bash
# Brevo API key (Brevo dashboard → Settings → API Keys)
aws ssm put-parameter \
  --name /siteforge/serenity-therapy/brevo_api_key \
  --value "xkeysib-YOUR_KEY" \
  --type SecureString

# JWT secret (auto-created by siteforge create, but verify it exists)
aws ssm get-parameter \
  --name /siteforge/serenity-therapy/jwt_secret \
  --with-decryption
```

### 9. Set up Brevo (see 02-brevo-setup-guide.md)

Then update `sites/serenity-therapy/site-config.json` with real Brevo template IDs.

### 10. Deploy frontend

```bash
python -m cli.siteforge deploy --id serenity-therapy
```

### 11. Seed default data (once seed.py is written — next session)

```bash
python -m cli.siteforge seed --id serenity-therapy
```

### 12. Local frontend dev

```bash
SITE_ID=serenity-therapy npm run dev -w apps/frontend
# → http://localhost:3000
```

---

## Recommended VS Code Extensions

```
ms-python.python
ms-python.black-formatter
dbaeumer.vscode-eslint
esbenp.prettier-vscode
bradlc.vscode-tailwindcss
amazonwebservices.aws-toolkit
```

### `.vscode/settings.json`

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "tailwindCSS.experimental.classRegex": [
    ["clsx\\(([^)]*)\\)", "'([^']*)'"]
  ]
}
```

---

## Brevo Pre-Launch Checklist

- [ ] Account created with business address in profile
- [ ] Sending domain added and verified (all DNS records green)
- [ ] Sender addresses created: `hello@`, `admin@`, `noreply@`
- [ ] All 8 email templates created, IDs recorded in site-config.json
- [ ] Conversations inbox connected to `admin@` email
- [ ] Admin notified with Brevo login credentials
- [ ] API key stored in SSM
- [ ] End-to-end test: register → verify email → book → admin alert received

---

## Session Stats

| Category | Count |
|---|---|
| Documents produced | 4 (3 guides + 1 spec) |
| Files in monorepo | 63 |
| Frontend pages | 12 across 4 route groups |
| API endpoints | 25+ across 7 handler modules |
| CDK stacks | 2 (Shared + Site) |
| CLI commands | 4 of 7 |
| Languages supported | EN + ES (extensible) |
| Target cost | < $2/site/month |
| Estimated scaffold hours saved | ~60h |
