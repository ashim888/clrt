# CLRT — Client Lifecycle & Revenue Tracker

> **MVP** · Django 5 · SQLite (swap-ready for PostgreSQL) · Tailwind CSS (CDN)

---

## Quick Start

```bash
# 1. Clone / open the project folder
cd clrt

# 2. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env file (optional, defaults work for dev)
cp .env.example .env

# 5. Run migrations
python manage.py migrate

# 6. Create admin user (or use the seeded one below)
python manage.py createsuperuser

# 7. Start the server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## Pre-Seeded Accounts

| Username    | Password   | Role     |
|-------------|------------|----------|
| `admin`     | `admin123` | Admin    |
| `sales1`    | `demo123`  | Sales    |
| `accounts1` | `demo123`  | Accounts |

---

## Project Structure

```
clrt/
├── core/               # Django project settings & root URLs
├── accounts/           # Custom User model, roles, login/logout
├── leads/              # Lead + Activity (Mini CRM)
├── clients/            # Client + Contract (with file upload)
├── billing/            # Invoice + Payment (manual entry)
├── dashboard/          # Overview dashboard + alerts management command
├── templates/          # All HTML templates (Tailwind CSS)
├── static/             # Static files
├── media/              # Uploaded contract documents
├── requirements.txt
└── manage.py
```

---

## Modules

### 1. Leads (`/leads/`)
- Create / edit / delete leads
- Status pipeline: New → Contacted → Demo → Negotiation → Won → Lost
- Log activities (call / meeting / follow-up / email) with next follow-up date
- Convert Won leads → Client (single click)

### 2. Clients (`/clients/`)
- Created automatically from lead conversion or manually
- Each client has Contracts with file uploads (PDF / image)
- Contract value, billing cycle, start/end dates, expiry alerts

### 3. Billing (`/billing/`)
- Manual invoice creation linked to client + contract
- Record partial or full payments
- Auto-detect overdue (click "Mark Overdue" or run management command)

### 4. Dashboard (`/`)
- Today's follow-ups
- Overdue follow-ups
- Contracts expiring within 30 days
- Pending / overdue invoices
- Monthly revenue summary

---

## Role Permissions

| Feature          | Sales | Accounts | Admin |
|------------------|-------|----------|-------|
| View leads       | ✅    | ❌       | ✅    |
| Create/edit leads| ✅    | ❌       | ✅    |
| View clients     | ✅    | ✅       | ✅    |
| Create clients   | ❌    | ✅       | ✅    |
| Contracts        | View  | ✅       | ✅    |
| Invoices         | View  | ✅       | ✅    |
| Dashboard        | ✅    | ✅       | ✅    |
| User management  | ❌    | ❌       | ✅    |

---

## Daily Alerts (Cron Job)

```bash
# Run manually anytime:
python manage.py check_alerts

# Schedule via cron (daily at 9 AM):
0 9 * * * /path/to/clrt/venv/bin/python /path/to/clrt/manage.py check_alerts
```

The command:
- Marks overdue invoices automatically
- Prints today's follow-ups
- Lists contracts expiring within 30 days

---

## Switching to PostgreSQL

1. Install: `pip install psycopg2-binary`
2. Update `core/settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "clrt_db",
        "USER": "postgres",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

3. Run: `python manage.py migrate`

---

## Django Admin

Access at **http://127.0.0.1:8000/admin/** with the `admin` account.

---

## Phase 2 (Excluded from MVP)

- Auto-invoice generation (cron-based)
- OCR for contract parsing
- WhatsApp / email notifications
- Advanced analytics & charts

