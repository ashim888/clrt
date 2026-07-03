# CLRT Documentation

**CLRT** (Client Relationship Tracker) is a self-hosted CRM covering the full revenue cycle — lead capture → pipeline → client management → invoicing → payment collection — built with Django 5.1 and Tailwind CSS.

---

## Table of Contents

| File | What it covers |
|---|---|
| [setup.md](setup.md) | Installation, first run, creating the admin user |
| [configuration.md](configuration.md) | Environment variables, `.env` reference, SiteSettings |
| [auth-2fa.md](auth-2fa.md) | User roles, login, two-factor authentication |
| [automation.md](automation.md) | Follow-up reminders, management command, cron setup |
| [landing-marketing.md](landing-marketing.md) | Landing page, contact form, analytics tracking, GA4 |
| [subscriptions.md](subscriptions.md) | Plans, feature flags, subscription model, feature gating |
| [features/leads.md](features/leads.md) | Lead pipeline, bulk operations, import/export |
| [features/clients.md](features/clients.md) | Client management, portal, contracts, bulk operations |
| [features/billing.md](features/billing.md) | Invoicing, Razorpay payments |
| [features/reports.md](features/reports.md) | Reports, analytics, sales velocity |
| [features/calendar.md](features/calendar.md) | Calendar events, follow-up scheduling |
| [features/proposals.md](features/proposals.md) | Quotes and proposals |
| [features/catalog.md](features/catalog.md) | Product/service catalog |
| [development.md](development.md) | Conventions, adding features, template patterns |

---

## Quick start

```bash
git clone <repo>
cd clrt
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install pyotp qrcode[pil]   # 2FA dependencies
cp .env.example .env            # edit as needed
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://localhost:8000` — unauthenticated visitors see the landing page; authenticated users go straight to the dashboard.

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Django 5.1, Python 3.11+ |
| Database | SQLite (dev) |
| Frontend | Tailwind CSS via CDN, vanilla JS |
| Auth | Django auth + custom TOTP 2FA (`pyotp`) |
| Charts | Chart.js 4.4 |
| Calendar | FullCalendar.js 6.1 |
| Payments | Razorpay (optional) |
| Email | SMTP / console backend |
| Static files | WhiteNoise |
