# Leads

---

## Models

### `Lead`

| Field | Notes |
|---|---|
| `organization_name` | Company / business name |
| `contact_person` | Primary contact name |
| `phone` | Phone number |
| `email` | Email address |
| `source` | `referral / website / linkedin / cold_call / social_media / event / partner / other` |
| `deal_value` | Decimal — optional; powers pipeline value reports and weighted forecast |
| `status` | `new / contacted / demo / negotiation / won / lost` |
| `lost_reason` | Free text — captured when marking lost; shown in Lost Reasons report |
| `assigned_to` | FK to `accounts.User` |
| `tags` | M2M to `dashboard.Tag` |
| `notes` | Free text |

### `Activity`

Logged interactions on a lead.

| Field | Notes |
|---|---|
| `lead` | FK to Lead |
| `type` | `call / meeting / follow_up / email` |
| `notes` | What happened / what was discussed |
| `next_follow_up_date` | Date — triggers reminder when due |
| `status` | `pending / completed / cancelled / rescheduled` |
| `resolution_note` | Filled when completing or cancelling |
| `created_by` | FK to User |
| `attachment` | File upload (optional) |

---

## Pipeline stages

```
New → Contacted → Demo → Negotiation → Won
                                     ↘ Lost
```

Stage probability weights (used in weighted forecast):

| Stage | Probability |
|---|---|
| New | 10% |
| Contacted | 25% |
| Demo | 50% |
| Negotiation | 75% |
| Won | 100% |
| Lost | 0% |

---

## Views & URLs (`leads` app)

| URL | View | Description |
|---|---|---|
| `/leads/` | `lead_list` | Paginated list with filters, sort, bulk actions |
| `/leads/add/` | `lead_create` | Create form (admin/sales only) |
| `/leads/<pk>/` | `lead_detail` | Detail + activity timeline |
| `/leads/<pk>/edit/` | `lead_edit` | Edit form |
| `/leads/<pk>/delete/` | `lead_delete` | Delete (admin only) |
| `/leads/<pk>/status/` | `lead_update_status` | AJAX inline status change (POST) |
| `/leads/<pk>/convert/` | `convert_to_client` | Convert won lead to client |
| `/leads/<pk>/activity/add/` | `activity_add` | Log activity on lead |
| `/leads/bulk/` | `lead_bulk_action` | Bulk operations (POST) |
| `/leads/export/` | `lead_export_csv` | CSV export of all leads |
| `/leads/import/` | `lead_import` | CSV import (admin/sales only) |
| `/leads/kanban/` | `lead_kanban` | Kanban board view |
| `/leads/capture/` | `lead_capture` | Public embeddable lead form (no login) |

---

## Bulk operations

Select leads using checkboxes on the list view. A floating action bar appears at the bottom of the screen.

### Available actions

| Action | Description |
|---|---|
| **Status** | Change all selected leads to any pipeline stage |
| **Assign** | Assign to a team member (or unassign) |
| **Tag → Add** | Add a tag to all selected |
| **Tag → Remove** | Remove a tag from all selected |
| **Delete** | Permanently delete (admin only) |

### Backend endpoint

`POST /leads/bulk/`

Form-encoded body:

```
action=status&value=contacted&ids=1&ids=2&ids=5
action=assign&value=3&ids=1&ids=2
action=tag_add&value=7&ids=1&ids=2
action=tag_remove&value=7&ids=1
action=delete&ids=1&ids=2
```

Returns `{"ok": true, "count": N}` on success.

---

## CSV import

**URL:** `/leads/import/` (admin/sales only)

Expected CSV columns:

```
organization_name, contact_person, phone, email, source, deal_value, notes, status
```

- `source` must be one of: `referral / website / linkedin / cold_call / social_media / event / partner / other`
- `status` must be one of: `new / contacted / demo / negotiation / won / lost`
- `deal_value` must be a number (no currency symbols)
- Missing/invalid rows are skipped with a warning

---

## Web lead capture form

**URL:** `/leads/capture/`

Public, no-login form that creates a `Lead` with `source="website"`. Embed on your website as an `<iframe>` or direct link. Thank-you page at `/leads/capture/thanks/`.

---

## Duplicate detection

Before saving a new lead, the create form POSTs to `/leads/check-duplicate/` and warns if a lead with the same phone or email already exists.

---

## Lost reason tracking

When a lead is moved to `lost` status (either via inline status select or bulk action), a modal prompts for a reason. This is stored in `Lead.lost_reason` and aggregated in the **Lost Reasons** report on the Reports page.

---

## Converting a lead to a client

Once a lead is `won`, a **Convert to Client** button appears on the lead detail page (`/leads/<pk>/convert/`). This:

1. Creates a `Client` record pre-filled from the lead
2. Sets `client.linked_lead = lead`
3. Redirects to the new client's detail page

The lead is preserved — it is not deleted.
