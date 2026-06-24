# AWS SES Production Access Request — Template

> Submit this via: AWS Console → SES → Account Dashboard → "Request Production Access"  
> Or via AWS Support Center → Create Case → Service Limit Increase → SES

---

## How to Submit

1. Log into AWS Console
2. Navigate to **Amazon SES → Account Dashboard**
3. Click **"Request Production Access"**
4. Fill in the form using the content below
5. Alternatively: Support Center → Create Case → Service Limit Increase → SES Sending Limits

Expected approval time: **24–48 hours** (often faster)

---

## Form Field Answers

### Mail Type
```
Transactional
```

### Website URL
```
https://[yourdomain.com]
```

### Use Case Description

Copy and adapt the following:

---

**Use Case Description (paste into AWS form):**

We operate a multi-tenant website platform that provides appointment booking services for small businesses. Each website on our platform serves a specific business (such as a salon, clinic, or consulting firm) and allows their customers to register, book appointments, and receive service-related communications.

Our transactional email use cases are:

1. **Account verification** — When a new user registers, we send a one-time verification link to confirm their email address before activating their account.

2. **Appointment confirmation** — When a user books an appointment, we send an immediate confirmation email containing appointment details (date, time, service, business location).

3. **Appointment status updates** — When an admin accepts, declines, or reschedules an appointment, the user receives an automated notification with the updated status.

4. **Password reset** — Users who forget their password receive a secure time-limited reset link via email.

5. **Appointment reminders** — 24 hours before a scheduled appointment, users receive an automated reminder email.

All emails are triggered by explicit user actions or scheduled system events. We do not send unsolicited marketing email through SES. Email campaigns are handled through a separate dedicated platform (Brevo).

Our platform is built on AWS Lambda and API Gateway. Emails are sent programmatically via the boto3 SES SDK from our Lambda functions. Each business website on our platform has its own verified sending domain.

---

### Describe How You Will Handle Bounces and Complaints

```
We handle bounces and complaints through SES SNS notifications as follows:

1. SES is configured to publish bounce and complaint events to an SNS topic.
2. An SNS subscription triggers a Lambda function that processes these events.
3. Hard bounces: the recipient email is immediately flagged in our DynamoDB 
   database and removed from all future sends.
4. Soft bounces: logged and monitored; after 3 consecutive soft bounces the 
   address is suppressed.
5. Complaints: the address is immediately added to our suppression list and 
   the user account is flagged.
6. All transactional emails include a clear sender identity and support 
   contact. Password reset and verification emails include instructions for 
   users who did not request them.
7. We maintain a global suppression list in DynamoDB shared across all 
   Lambda functions.
```

### How Do You Comply with Anti-Spam Laws?

```
We comply with CAN-SPAM, CASL, and GDPR requirements as follows:

1. All emails are transactional and sent only to users who explicitly 
   created an account or took an action on our platform.
2. Every email includes our business name and a physical or registered 
   mailing address in the footer.
3. Users can delete their account at any time, which triggers immediate 
   removal from all future sends.
4. We do not purchase, rent, or scrape email lists.
5. Sending domain and From address are clearly identified and match our 
   registered business domain.
6. We maintain records of user consent (registration timestamp, IP, 
   action taken) in DynamoDB.
```

---

## Pre-Submission Checklist

Before submitting, complete these steps or AWS may reject/delay:

- [ ] Verify your sending domain in SES (add DKIM + TXT records in Cloudflare)
- [ ] Verify at least one From address (e.g. `noreply@yourdomain.com`)
- [ ] Set up SNS topic for bounce/complaint notifications
- [ ] Create a Lambda function stub to handle bounce/complaint SNS events
- [ ] Confirm your website is live or has a working staging URL to include

---

## Post-Approval Steps

Once approved (you'll receive an email from AWS):

1. **Remove sandbox restriction** — your account can now send to any address
2. **Set up configuration set** in SES for tracking opens/clicks (optional)
3. **Update site-config.json** — change `email.provider` from `"brevo"` to `"ses"`
4. **Monitor sending reputation** — SES Console → Reputation Dashboard
5. **Set CloudWatch alarm** on bounce rate > 2% and complaint rate > 0.1%

---

## SES DNS Records to Add in Cloudflare

After verifying your domain in SES, add these records:

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| TXT | `_amazonses.yourdomain.com` | (provided by AWS) | Domain verification |
| CNAME | `xxx._domainkey.yourdomain.com` | (provided by AWS) | DKIM key 1 |
| CNAME | `yyy._domainkey.yourdomain.com` | (provided by AWS) | DKIM key 2 |
| CNAME | `zzz._domainkey.yourdomain.com` | (provided by AWS) | DKIM key 3 |
| TXT | `yourdomain.com` | `v=spf1 include:amazonses.com ~all` | SPF record |

> All values are generated by AWS SES during domain verification — copy them exactly from the SES console.

---

*Template version 1.0 — Adapt [yourdomain.com] to your actual domain before submitting*
