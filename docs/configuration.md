# Configuration Reference

All runtime configuration is loaded from a `.env` file in the project root via `python-dotenv`. Settings fall back to safe development defaults if not set.

---

## Environment variables

### Core Django

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-clrt-dev-secret` | **Change in production.** Django secret key. |
| `DEBUG` | `True` | Set `False` in production. |

### Email

| Variable | Default | Description |
|---|---|---|
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Use `django.core.mail.backends.smtp.EmailBackend` in production. |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server hostname. |
| `EMAIL_PORT` | `587` | SMTP port. |
| `EMAIL_USE_TLS` | `True` | TLS encryption. |
| `EMAIL_HOST_USER` | _(empty)_ | SMTP username / Gmail address. |
| `EMAIL_HOST_PASSWORD` | _(empty)_ | SMTP password or Gmail App Password. |
| `DEFAULT_FROM_EMAIL` | `CLRT <noreply@clrt.app>` | Sender address on outbound emails. |
| `ADMIN_EMAIL` | _(empty)_ | Receives daily digests: overdue invoices, expiring contracts. |
| `SITE_URL` | `http://localhost:8000` | Base URL used in reminder email links. Set to your public domain in production. |

> **Gmail setup:** Enable 2-Step Verification on your Google account, then generate an **App Password** at `myaccount.google.com/apppasswords`. Use that as `EMAIL_HOST_PASSWORD`.

### Example `.env` (production)

```env
SECRET_KEY=replace-with-50-char-random-string
DEBUG=False
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=yourname@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=CLRT <yourname@gmail.com>
ADMIN_EMAIL=yourname@gmail.com
SITE_URL=https://yourdomain.com
```

---

## SiteSettings (in-app)

Some configuration lives in the database and is editable via **Django Admin → Dashboard → Site Settings** or the in-app **Settings** page (`/settings/`).

| Field | Description |
|---|---|
| `currency_symbol` | Rs. / ₹ / NPR / $ / £ / € / ¥ — shown on invoices and reports |
| `number_format` | `indian` (1,50,000) or `western` (150,000) |
| `date_format` | Display format for dates across the app |
| `fiscal_year_start` | Month number (1=Jan, 4=Apr) — affects fiscal year reports |
| `business_name` | Appears on invoices and the client portal |
| `business_tagline` | Subtitle on invoices |
| `business_address` | Printed on invoice footer |
| `business_phone / email / website` | Contact info on invoices |
| `tax_number` | GST / VAT / PAN shown on documents |
| `invoice_prefix` | Prefix for auto-generated invoice numbers (default: `INV`) |
| `quote_prefix` | Prefix for quote numbers (default: `Q`) |
| `default_tax_rate` | Default tax % applied to new invoices and quotes |
| `default_payment_terms` | Boilerplate text on invoices |
| `razorpay_key_id` | Razorpay public key (Growth / Enterprise only) |
| `razorpay_key_secret` | Razorpay secret key |
| `razorpay_enabled` | Toggle Razorpay payment links on invoices |
| `ga_measurement_id` | Google Analytics 4 Measurement ID (e.g. `G-XXXXXXXXXX`) — injected on the landing page |

---

## Hardcoded settings (in `core/settings.py`)

| Setting | Value | Notes |
|---|---|---|
| `TIME_ZONE` | `Asia/Kathmandu` | All datetimes stored as UTC, displayed in this timezone. Change to `Asia/Kolkata` for India-only deployments. |
| `USE_TZ` | `True` | Timezone-aware datetimes throughout. Do not disable. |
| `DATABASE` | SQLite (`db.sqlite3`) | Switch to PostgreSQL for production multi-user deployments. |
| `AUTH_USER_MODEL` | `accounts.User` | Custom user model with `role` and TOTP fields. |
| `LOGIN_URL` | `/accounts/login/` | |
| `LOGIN_REDIRECT_URL` | `/` | Goes to dashboard (or landing page if unauthenticated). |
| `LOGOUT_REDIRECT_URL` | `/accounts/login/` | |

---

## Timezone handling

All `DateTimeField` values are stored in UTC. When displaying dates or filtering by date range, always use `django.utils.timezone.localtime()` to convert to `settings.TIME_ZONE` first.

```python
from django.utils import timezone
local_dt = timezone.localtime(some_utc_datetime)
display_str = local_dt.strftime("%Y-%m-%d")
```

Never call `.strftime()` directly on a UTC datetime — it will show the wrong date for UTC+ timezones.
