# Brevo Setup Guide — Client Onboarding for Webmasters

> This guide is for webmasters setting up and managing Brevo accounts on behalf of client websites on the SiteForge platform. Follow these steps for each new client site.

---

## Table of Contents

1. [What is Brevo and Why We Use It](#1-what-is-brevo-and-why-we-use-it)
2. [Creating the Client Account](#2-creating-the-client-account)
3. [Domain & Email Verification](#3-domain--email-verification)
4. [Cloudflare DNS Configuration](#4-cloudflare-dns-configuration)
5. [Getting the API Key](#5-getting-the-api-key)
6. [Configuring the SiteForge Platform](#6-configuring-the-siteforge-platform)
7. [Setting Up the Admin Inbox (Conversations)](#7-setting-up-the-admin-inbox-conversations)
8. [Email Templates Setup](#8-email-templates-setup)
9. [Email Campaigns Setup (Optional)](#9-email-campaigns-setup-optional)
10. [WhatsApp Business Setup (Future)](#10-whatsapp-business-setup-future)
11. [Handoff to Client](#11-handoff-to-client)
12. [Ongoing Management Checklist](#12-ongoing-management-checklist)

---

## 1. What is Brevo and Why We Use It

Brevo (formerly Sendinblue) is an all-in-one communication platform that replaces what cPanel's built-in mail server + MailChimp + a help desk would normally require separately.

**What we use Brevo for on each client site:**

| Feature | Purpose |
|---|---|
| Transactional SMTP/API | Send automated emails: account verification, appointment confirmations, password resets, reminders |
| Conversations (Inbox) | Admin receives and replies to user emails from one dashboard |
| Contact list sync | User registrations are synced as contacts for future campaigns |
| Email campaigns | Client can send newsletters or promotions to their user base |
| WhatsApp API (future) | Appointment notifications via WhatsApp |

**Brevo Free Plan includes:**
- 300 emails/day (9,000/month)
- Unlimited contacts
- 1 shared inbox (Conversations)
- Basic email campaign editor
- SMTP + REST API access

This is sufficient for most new client sites. Paid plans start at $9/month if they exceed 300/day.

---

## 2. Creating the Client Account

### Option A — Client Creates Their Own Account (Recommended)

1. Client goes to **https://app.brevo.com/account/register**
2. Signs up with their **business email** (e.g. `owner@clientdomain.com`)
3. Chooses **"Marketing & Transactional Email"** as use case
4. Skips the onboarding wizard for now
5. Shares login credentials securely with you (webmaster)

### Option B — Webmaster Creates on Behalf of Client

1. Use a dedicated email like `brevo+clientname@youragency.com`
2. Create account at https://app.brevo.com
3. Add client as a **user** under Settings → Users & Activity
4. Grant client **"Admin"** role
5. Document credentials in your password manager

### Account Settings to Configure Immediately

```
Settings → Company → Fill in:
  - Company name: [Client business name]
  - Address: [Client physical address]  ← Required for CAN-SPAM compliance
  - Website: https://[clientdomain.com]
  - Phone: [Client phone]
```

> ⚠️ The physical address appears in every email footer. Use the client's real business address, not a PO Box.

---

## 3. Domain & Email Verification

This step allows Brevo to send emails **from** the client's domain (e.g. `noreply@clientdomain.com`).

### Step 1 — Add Sending Domain

1. In Brevo: **Settings → Senders & IP → Domains**
2. Click **"Add a domain"**
3. Enter the client's domain: `clientdomain.com`
4. Click **"Save and proceed"**
5. Brevo displays DNS records to add — **keep this tab open**

### Step 2 — Add Sender Address

1. **Settings → Senders & IP → Senders**
2. Click **"Add a new sender"**
3. Fill in:
   - **Name:** Client Business Name (or "Appointments Team")
   - **Email:** `noreply@clientdomain.com`
4. Save

Repeat for:
- `admin@clientdomain.com` (for admin notifications)
- `hello@clientdomain.com` (for campaigns, optional)

---

## 4. Cloudflare DNS Configuration

After generating DNS records in Brevo (Step 3 above), add them in Cloudflare.

### Login to Cloudflare

1. Go to https://dash.cloudflare.com
2. Select the client's domain
3. Go to **DNS → Records**

### Records to Add

Brevo provides exact values — use those. The record types are:

| Type | Name | Value | Purpose | Proxy |
|------|------|-------|---------|-------|
| TXT | `@` or `clientdomain.com` | `brevo-code:xxxxxxxxx` | Domain ownership verification | DNS only ☁️ |
| TXT | `@` | `v=spf1 include:spf.brevo.com ~all` | SPF — authorize Brevo to send | DNS only ☁️ |
| CNAME | `mail._domainkey` | `mail._domainkey.brevo.com` | DKIM signature | DNS only ☁️ |
| CNAME | `brevo._domainkey` | `brevo._domainkey.brevo.com` | DKIM signature 2 | DNS only ☁️ |

> ⚠️ **Important:** Set all these records to **"DNS only"** (grey cloud), NOT proxied (orange cloud). Proxying breaks email authentication.

### MX Records (for admin inbox — receives email)

If the client wants `admin@clientdomain.com` to receive emails via Brevo Conversations:

| Type | Name | Priority | Value |
|------|------|----------|-------|
| MX | `@` | 10 | `inbound.brevo.com` |

> ⚠️ If client already has MX records (e.g. from Google Workspace or Zoho), do NOT replace them. Use a subdomain instead: `replies@mail.clientdomain.com` with MX pointing to `inbound.brevo.com`.

### Verify in Brevo

1. Back in Brevo: **Settings → Senders & IP → Domains**
2. Click **"Verify"** next to the domain
3. All checkmarks should turn green within 5–30 minutes
4. If stuck: double-check no Cloudflare proxy on the records, wait up to 1 hour for propagation

---

## 5. Getting the API Key

The SiteForge platform uses the Brevo API to send emails programmatically from Lambda.

1. In Brevo: **Settings → API Keys**
2. Click **"Generate a new API key"**
3. Name it: `siteforge-[clientname]-prod`
4. Copy the key — **it only shows once**
5. Store it in AWS SSM Parameter Store:

```bash
aws ssm put-parameter \
  --name "/siteforge/[site_id]/brevo_api_key" \
  --value "xkeysib-xxxxxxxxxxxx" \
  --type "SecureString" \
  --region us-east-1
```

6. Also store the sender address:

```bash
aws ssm put-parameter \
  --name "/siteforge/[site_id]/brevo_sender_email" \
  --value "noreply@clientdomain.com" \
  --type "SecureString"
```

---

## 6. Configuring the SiteForge Platform

Update the client's `site-config.json`:

```json
"email": {
  "provider": "brevo",
  "senderName": "Client Business Name",
  "senderEmail": "noreply@clientdomain.com",
  "adminEmail": "admin@clientdomain.com",
  "apiKeyParam": "/siteforge/[site_id]/brevo_api_key"
}
```

Run the siteforge config update:

```bash
siteforge config --id [site_id] --set email.provider=brevo
siteforge deploy --id [site_id]
```

Test by triggering a test registration on the site and confirming the email arrives.

---

## 7. Setting Up the Admin Inbox (Conversations)

This gives the client a unified inbox where they receive appointment notifications and can reply to users.

### Enable Conversations

1. In Brevo: Left sidebar → **Conversations**
2. Click **"Get started"**
3. Choose **"Email"** channel
4. Connect the inbox email: `admin@clientdomain.com`
5. Set display name: `[Business Name] Team`

### Configure Notifications

1. **Conversations → Settings → Notifications**
2. Enable:
   - Email notification when new message arrives
   - Browser notification (optional)
3. Set notification email to the client's personal email so they're alerted even when not logged into Brevo

### Train the Client on Conversations

Show the client how to:
- View the inbox at https://app.brevo.com (or mobile app)
- Reply to a user message (their reply goes to `user@gmail.com`)
- Mark conversations as resolved
- Assign conversations to a team member (future)

---

## 8. Email Templates Setup

Create these templates in Brevo so the platform can reference them by ID.

### Navigate to Templates

**Email Campaigns → Templates → "Create a template"**

### Template 1 — Account Verification

- **Name:** `siteforge-verify-email`
- **Subject:** `Verify your email — [Business Name]`
- **From:** `noreply@clientdomain.com`

**Body (adapt as needed):**
```
Hi {{params.firstName}},

Welcome to [Business Name]! Please verify your email address to activate your account.

[VERIFY MY EMAIL]  ← Button linking to {{params.verificationUrl}}

This link expires in 24 hours.
If you didn't create an account, you can safely ignore this email.

— [Business Name] Team
```

### Template 2 — Appointment Confirmation (User)

- **Name:** `siteforge-appt-confirmed`
- **Subject:** `Appointment confirmed — {{params.serviceName}}`

**Body:**
```
Hi {{params.firstName}},

Your appointment has been confirmed!

Service:   {{params.serviceName}}
Date:      {{params.date}}
Time:      {{params.time}}
Location:  {{params.location}}

Need to cancel? You can manage your appointment at:
{{params.appointmentUrl}}

— [Business Name] Team
```

### Template 3 — Appointment Notification (Admin)

- **Name:** `siteforge-appt-admin-alert`
- **Subject:** `New appointment request from {{params.userName}}`

**Body:**
```
New appointment request received:

Customer:  {{params.userName}} ({{params.userEmail}})
Phone:     {{params.userPhone}}
Service:   {{params.serviceName}}
Requested: {{params.date}} at {{params.time}}
Notes:     {{params.notes}}

[VIEW IN DASHBOARD]  ← Button linking to {{params.dashboardUrl}}

Reply to this email to contact the customer directly.
```

### Template 4 — Appointment Reminder

- **Name:** `siteforge-appt-reminder`
- **Subject:** `Reminder: Your appointment tomorrow at {{params.time}}`

### Template 5 — Password Reset

- **Name:** `siteforge-password-reset`
- **Subject:** `Reset your password — [Business Name]`

### Record Template IDs

After saving each template, note the numeric ID (visible in the URL or template list). Add to site config:

```json
"emailTemplates": {
  "verifyEmail": 1,
  "appointmentConfirmed": 2,
  "appointmentAdminAlert": 3,
  "appointmentReminder": 4,
  "passwordReset": 5
}
```

---

## 9. Email Campaigns Setup (Optional)

For clients who want to send newsletters or promotions to their registered users.

### Enable Contact Sync

The SiteForge platform automatically syncs new user registrations to Brevo contacts. Verify this is working:

1. Brevo → **Contacts**
2. After a test registration, the user should appear here
3. They are tagged with the list: `[site_id]-users`

### Create a Campaign List

1. **Contacts → Lists → "Create a list"**
2. Name: `[Business Name] Users`
3. This list auto-populates from registrations

### Sending a Campaign (Client Instructions)

1. **Email Campaigns → Create a campaign**
2. Choose **"Regular campaign"**
3. Select list: `[Business Name] Users`
4. Use the drag-and-drop editor or HTML
5. Schedule or send immediately
6. Monitor open rate, click rate in campaign report

> Note for clients: Free plan allows 300 emails/day. For a campaign to 500 contacts, schedule it to send over 2 days, or upgrade to Starter plan ($9/mo) for 20,000/month.

---

## 10. WhatsApp Business Setup (Future)

When the client is ready to add WhatsApp notifications:

### Prerequisites

- Client must have a **WhatsApp Business Account** (via Meta Business Manager)
- A dedicated phone number not linked to personal WhatsApp
- Business must be approved by Meta (usually 1–3 days)

### Steps

1. Brevo → **Settings → WhatsApp**
2. Connect Meta Business Manager account
3. Submit WhatsApp Business API access request
4. Once approved, create message templates in Meta (required for outbound messages)
5. Update site-config.json:

```json
"whatsapp": {
  "enabled": true,
  "provider": "brevo",
  "phoneNumberId": "{{META_PHONE_NUMBER_ID}}"
}
```

### WhatsApp Use Cases (Planned)

| Trigger | Message |
|---|---|
| Appointment confirmed | "Hi [Name], your [Service] is confirmed for [Date] at [Time]. Reply CANCEL to cancel." |
| Appointment reminder | "Reminder: You have [Service] tomorrow at [Time] with [Business]." |
| Status update | "Your appointment has been [accepted/rescheduled]. Check details: [URL]" |

---

## 11. Handoff to Client

Once setup is complete, provide the client with:

### Client Credentials Document (fill and share securely)

```
BREVO ACCOUNT
  URL:       https://app.brevo.com
  Email:     [their email]
  Password:  [stored in password manager - share via 1Password / Bitwarden]

WHAT YOU CAN DO IN BREVO:
  ✅ View and reply to customer messages (Conversations tab)
  ✅ Send email campaigns to your users
  ✅ View email delivery reports
  ✅ Download contact lists

WHAT YOUR WEBMASTER MANAGES:
  ⚙️  Email templates (technical setup)
  ⚙️  API configuration
  ⚙️  DNS records
  ⚙️  Contact sync settings

DAILY EMAIL LIMIT:  300 emails/day (free plan)
UPGRADE NEEDED IF: More than 300 user actions per day
UPGRADE COST:      $9/month (Starter plan, 20,000 emails/month)
```

### Train the Client On

- [ ] How to check the Conversations inbox for user messages
- [ ] How to reply to a user from the Brevo inbox
- [ ] How to create a simple email campaign
- [ ] What to do if they hit the daily send limit
- [ ] How to view delivery and open rate reports

---

## 12. Ongoing Management Checklist (Webmaster)

### Monthly

- [ ] Check Brevo sending reputation (Settings → Senders → Reputation)
- [ ] Review bounce rate — should stay below 2%
- [ ] Review complaint rate — should stay below 0.1%
- [ ] Check contact list growth matches site registrations
- [ ] Confirm all transactional emails are delivering (test registration)

### Per New Site Launch

- [ ] Create Brevo account
- [ ] Verify domain + senders
- [ ] Add Cloudflare DNS records
- [ ] Store API key in SSM Parameter Store
- [ ] Create all 5 email templates
- [ ] Record template IDs in site-config.json
- [ ] Configure Conversations inbox
- [ ] Test full flow: register → verify → book → confirm email received
- [ ] Hand off credentials + training to client

---

*Guide version 1.0 — SiteForge Platform*
