# Clients

---

## Models

### `Client`

| Field | Notes |
|---|---|
| `organization_name` | Company name |
| `email / phone` | Primary contact details |
| `industry` | Free text |
| `status` | `active / at_risk / inactive / churned` |
| `linked_lead` | FK to `leads.Lead` (set on convert) |
| `tags` | M2M to `dashboard.Tag` |
| `notes` | Free text |
| `portal_token` | UUID — unique URL for client self-service portal |

### `ClientContact`

Multiple contacts per client. Fields: `name`, `role`, `email`, `phone`, `is_primary`.

### `ClientInteraction`

Logged touchpoints with a client.

| Field | Notes |
|---|---|
| `client` | FK to Client |
| `type` | `call / email / meeting / other` |
| `summary` | What was discussed |
| `next_follow_up_date` | Triggers reminder when due |
| `follow_up_done` | Boolean — mark done from dashboard or client detail |
| `created_by` | FK to User |

### `Contract`

| Field | Notes |
|---|---|
| `client` | FK to Client |
| `title` | Contract title |
| `start_date / end_date` | Date range — expiry alerts fire 30 days before `end_date` |
| `value` | Contract value |
| `status` | `active / expired / terminated / draft` |
| `document` | File upload |

---

## Views & URLs (`clients` app)

| URL | View | Description |
|---|---|---|
| `/clients/` | `client_list` | List with filters, sort, bulk actions |
| `/clients/add/` | `client_create` | Create form (admin/accounts only) |
| `/clients/<pk>/` | `client_detail` | Detail: contacts, interactions, contracts, invoices |
| `/clients/<pk>/edit/` | `client_edit` | Edit form |
| `/clients/export/` | `client_export_csv` | CSV export |
| `/clients/bulk/` | `client_bulk_action` | Bulk operations (POST) |
| `/clients/<pk>/portal/regenerate/` | `portal_regenerate_token` | Generate new portal URL |
| `/clients/portal/<uuid:token>/` | `portal_home` | Public client portal (no login) |

---

## Bulk operations

Same pattern as leads. Floating action bar when checkboxes are selected.

| Action | Description |
|---|---|
| **Status** | `active / at_risk / inactive / churned` |
| **Tag → Add / Remove** | Tag management |
| **Delete** | Admin only |

**Endpoint:** `POST /clients/bulk/`

---

## Client portal

Each client gets a unique UUID URL:

```
/clients/portal/<uuid>/
```

The portal is **public** (no login required). It shows:
- Client name and status
- Active contracts and their status
- Invoices (paid / pending / overdue)
- Outstanding balance

**Regenerate the URL:** Client detail page → **Regenerate portal link** button. The old URL immediately becomes invalid.

Share the portal link with the client so they can check their status without logging into CLRT.

---

## Interaction follow-ups

When logging a `ClientInteraction` with a `next_follow_up_date`, it appears:
- On the main **dashboard** (Today's Agenda panel)
- In the daily reminder command (`send_followup_reminders`)
- On the client detail page as a pending item

Mark done from the dashboard or client detail via the **Mark done** button (AJAX).

---

## Contract expiry alerts

The `send_followup_reminders` command checks for contracts with `end_date` within 30 days and creates notifications for all admin users. Set `ADMIN_EMAIL` in `.env` to also receive an email digest.
