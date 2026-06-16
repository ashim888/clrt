🧾 PROJECT SPEC: Client Lifecycle & Revenue Tracker
===================================================

NOTE: Build this strictly as MVP. Do NOT add extra features. Follow schema and workflows exactly.

1\. 🎯 Objective
----------------

Build a **web-based application** that helps service businesses:

-   Track sales/marketing follow-ups
-   Manage AMC (recurring billing)
-   Store and manage contracts
-   Prevent missed revenue and missed follow-ups

* * * * *

2\. 🧠 Core Concept
-------------------

The system must revolve around a **Client Lifecycle Pipeline**:

Lead → Contact → Meeting → Follow-up → Deal Won → Contract → Billing → Renewal

Each module MUST be interconnected. No isolated modules.

* * * * *

3\. 👥 User Roles
-----------------

### Roles:

-   Admin
-   Sales/Marketing
-   Accounts
-   Super Admin (optional)

### Permissions:

| Module | Sales | Accounts | Admin |
| --- | --- | --- | --- |
| Leads | ✅ | ❌ | ✅ |
| Follow-ups | ✅ | ❌ | ✅ |
| Contracts | View | ✅ | ✅ |
| Billing (AMC) | ❌ | ✅ | ✅ |
| Dashboard | Partial | Partial | Full |

* * * * *

4\. 🧱 Core Modules
-------------------

* * * * *

MODULE 1: Lead & Follow-Up Management (Mini CRM)
------------------------------------------------

### Entities:

-   Lead
-   Contact Person
-   Activity (meeting/call/follow-up)

### Features:

-   Create/Edit Lead
-   Add meeting logs (date, notes, outcome)
-   Set follow-up date
-   Reminder system (in-app)

### Required Fields:

Lead:
- id
- organization_name
- contact_person
- phone
- email
- status (new/contacted/demo/negotiation/won/lost)
- assigned_to
- created_at

Activity:
- id
- lead_id
- type (call/meeting/follow-up)
- notes
- next_follow_up_date
- created_by
- created_at

### Logic:

-   Every activity can create a **next follow-up task**
-   Daily dashboard should show:
    -   Today's follow-ups
    -   Overdue follow-ups

* * * * *

MODULE 2: Client & Contract Management
--------------------------------------

### Entities:

-   Client (converted lead)
-   Contract

### Features:

-   Convert Lead → Client
-   Upload contract (image/PDF)
-   Tag contract details

### Required Fields:

Client:
- id
- organization_name
- linked_lead_id
- created_at

Contract:
- id
- client_id
- contract_title
- start_date
- end_date
- billing_cycle (monthly/quarterly/yearly)
- contract_value
- document_url
- status (active/expired)

### Logic:

-   Contract expiry triggers renewal alert
-   Contract defines billing behavior

* * * * *

MODULE 3: AMC / Recurring Billing System
----------------------------------------

### Entities:

-   Invoice
-   Payment

### Features:

-   Auto-generate invoices based on contract
-   Track payment status
-   Overdue alerts

### Required Fields:

Invoice:
- id
- client_id
- contract_id
- amount
- due_date
- status (pending/paid/overdue)
- generated_date

Payment:
- id
- invoice_id
- amount_paid
- payment_date
- payment_mode

### Logic:

-   Cron job / scheduler:
    -   Generate invoice based on billing_cycle
-   If unpaid after due_date → mark overdue
-   Dashboard alert for overdue invoices

* * * * *

MODULE 4: Dashboard & Alerts
----------------------------

### Dashboard Sections:

-   Today's Follow-Ups
-   Overdue Follow-Ups
-   Upcoming Renewals
-   Pending Payments
-   Revenue Summary

### Alerts:

-   Follow-up reminder
-   Contract expiry reminder
-   Payment overdue alert

* * * * *

5\. 🔄 Key Workflows (VERY IMPORTANT)
-------------------------------------

### Workflow 1: Lead to Client

Create Lead → Add Activities → Mark as "Won" → Convert to Client → Create Contract

* * * * *

### Workflow 2: Contract to Billing

Create Contract → Define billing cycle → System auto-generates invoices → Track payments

* * * * *

### Workflow 3: Renewal Loop

Contract nearing expiry → Alert → Sales follow-up → Renew → New contract cycle

* * * * *

6\. 🛠️ Technical Requirements
------------------------------

### Suggested Stack:

-   Frontend: HTML / CSS 
-   Backend: Django
-   Database: PostgreSQL
-   Storage: local storage (for contracts)

### APIs:

-   RESTful APIs for all modules
-   Auth (JWT-based)

* * * * *

7\. ⏰ Background Jobs (IMPORTANT)
---------------------------------

Implement scheduler (cron or worker):

### Jobs:

-   Daily at 9 AM:
    -   Fetch today's follow-ups
-   Daily:
    -   Check contract expiry (within 30 days)
-   Billing:
    -   Generate invoices automatically

* * * * *

8\. 📱 UX Requirements
----------------------

-   Simple, fast UI (NOT enterprise clutter)
-   Design Flavor: shadcn/ui
-   Mobile responsive (sales team usage)
-   Minimal clicks:
    -   Add lead in < 10 seconds
    -   Log activity in < 15 seconds


* * * * *

9\. 🚀 MVP Scope (STRICT)
-------------------------

Coding agent should ONLY build:

### Include:

-   Lead management + follow-ups
-   Client + contract upload
-   Manual invoice entry (no auto yet)
-   Dashboard (basic)

### Exclude (Phase 2):

-   OCR
-   WhatsApp integration
-   Auto invoice generation
-   Advanced analytics

* * * * *

10\. 📊 Success Criteria
------------------------

System is successful if:

-   No follow-up is missed
-   All contracts are searchable
-   No billing cycle is forgotten

* * * * *

11\. ⚠️ Constraints
-------------------

-   Avoid over-engineering
-   Keep schema flexible (future expansion)
-   Prioritize usability over features

* * * * *

12\. 📦 Deliverables
--------------------

Coding agent must provide:

-   Backend API
-   Backend UI
-   Frontend UI
-   Database schema
-   Setup instructions

* * * * *
