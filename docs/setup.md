# Setup & Installation

## Prerequisites

- Python 3.11+
- pip
- git

## 1. Clone and create virtualenv

```bash
git clone <repo-url> clrt
cd clrt
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
pip install pyotp "qrcode[pil]"   # two-factor auth (not in requirements.txt yet)
```

> **Note:** `pyotp` and `qrcode` are required for 2FA. Add them to `requirements.txt` when deploying.

## 3. Environment file

```bash
cp .env.example .env   # if .env.example exists, otherwise create .env manually
```

Minimum `.env` for local dev (everything else has safe defaults):

```env
SECRET_KEY=change-this-to-a-long-random-string
DEBUG=True
```

See [configuration.md](configuration.md) for all variables.

## 4. Run migrations

```bash
python manage.py migrate
```

This applies all migrations across all apps:
- `accounts` — User model + 2FA fields
- `leads` — Lead, Activity
- `clients` — Client, Contract, ClientInteraction, etc.
- `billing` — Invoice
- `proposals` — Quote
- `catalog` — Product/Service
- `dashboard` — SiteSettings, Tag, Notification, CalendarEvent, UserGoal, PageEvent, Plan, Subscription

## 5. Create superuser

```bash
python manage.py createsuperuser
```

The superuser has `is_superuser=True` which grants admin-level access everywhere regardless of the `role` field.

## 6. (Optional) Load sample plans

Plans power the subscription/pricing tier system. Create them via Django admin or shell:

```bash
python manage.py shell
```

```python
from dashboard.models import Plan

Plan.objects.create(
    name="Starter", slug="starter", tagline="Solo operators & small teams",
    price_monthly=999, price_yearly=9990,
    max_leads=100, max_clients=20, max_users=2, max_invoices=50,
    has_calendar=True,
    custom_features=["100 leads · 20 clients · 2 users", "Pipeline tracking", "Calendar & follow-ups", "Basic invoicing (50/month)"],
)
Plan.objects.create(
    name="Growth", slug="growth", tagline="For growing teams",
    price_monthly=2499, price_yearly=24990,
    max_leads=0, max_clients=100, max_users=5, max_invoices=0,
    has_reports=True, has_proposals=True, has_razorpay=True,
    has_client_portal=True, has_web_capture=True, has_quota_tracking=True,
    has_catalog=True, has_calendar=True,
    custom_features=["Unlimited leads · 100 clients · 5 users", "Reports & Analytics", "Client portal", "Online payments (Razorpay)", "Proposals & quotes", "Web lead capture", "Quota & goal tracking"],
)
Plan.objects.create(
    name="Enterprise", slug="enterprise", tagline="Unlimited everything",
    price_monthly=5999, price_yearly=59990,
    max_leads=0, max_clients=0, max_users=0, max_invoices=0,
    has_reports=True, has_proposals=True, has_razorpay=True,
    has_client_portal=True, has_web_capture=True, has_quota_tracking=True,
    has_audit_log=True, has_catalog=True, has_calendar=True, has_custom_branding=True,
    custom_features=["Everything in Growth", "Unlimited team members", "Audit trail & compliance", "Custom branding", "Dedicated onboarding", "SLA & priority support"],
)
```

## 7. Configure SiteSettings

Go to **Django Admin → Dashboard → Site Settings** (or `/admin/`) and fill in:

- Business name, address, phone, email
- Currency symbol and number format
- Invoice / quote prefix
- Default tax rate

## 8. Run the dev server

```bash
python manage.py runserver
```

Visit `http://localhost:8000`.

- **Unauthenticated** → landing page
- **Authenticated** → dashboard

---

## Folder structure

```
clrt/
├── accounts/          User model, login, 2FA views & middleware
├── billing/           Invoice model & views
├── catalog/           Product/service catalog
├── clients/           Client, Contract, ClientInteraction, portal
├── core/              settings.py, urls.py, wsgi.py
├── dashboard/         Dashboard, reports, calendar, SiteSettings, plans
├── leads/             Lead, Activity, management commands
├── proposals/         Quote model & views
├── templates/         All HTML templates
│   ├── accounts/
│   ├── billing/
│   ├── clients/
│   ├── dashboard/
│   ├── leads/
│   ├── partials/
│   └── proposals/
├── static/            CSS, JS, images
├── media/             Uploaded files
├── docs/              ← you are here
├── manage.py
├── requirements.txt
└── .env
```
