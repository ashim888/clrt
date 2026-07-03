# Proposals & Quotes

---

## Overview

Create branded quotes/proposals to send to leads or clients before issuing a formal invoice.

**Requires:** `has_proposals=True` on the current plan (Growth / Enterprise)

**URL prefix:** `/proposals/`

---

## Model (`proposals.models.Quote`)

| Field | Notes |
|---|---|
| `client` | FK to `clients.Client` |
| `quote_number` | Auto-generated: `{quote_prefix}-{YYYY}-{N}` e.g. `Q-2025-001` |
| `title` | Quote title / subject |
| `generated_date` | Date issued |
| `valid_until` | Expiry date |
| `status` | `draft / sent / accepted / rejected / expired` |
| `subtotal` | Auto-calculated from line items |
| `tax_rate` | Tax % (defaults from SiteSettings) |
| `tax_amount` | Auto-calculated |
| `total` | `subtotal + tax_amount` |
| `notes` | Internal notes |
| `terms` | Terms printed on the quote |

### Line items (`proposals.models.QuoteItem`)

| Field | Notes |
|---|---|
| `quote` | FK to Quote |
| `description` | Item description |
| `quantity` | Decimal |
| `unit_price` | Decimal |
| `total` | `quantity × unit_price` (auto-calculated) |

---

## Workflow

```
Draft → Sent → Accepted → (convert to invoice)
                ↘ Rejected
       ↘ Expired (past valid_until)
```

1. Create a quote (draft)
2. Send to client (mark as Sent)
3. On acceptance → **Convert to Invoice** button creates an `Invoice` pre-filled from the quote
4. Rejected or expired quotes remain for reference

---

## Print view

`/proposals/<pk>/print/` — clean printable layout matching invoice print style. Uses business name/address from SiteSettings.

---

## URLs

| URL | Description |
|---|---|
| `/proposals/` | Quote list |
| `/proposals/add/` | Create quote |
| `/proposals/<pk>/` | Quote detail |
| `/proposals/<pk>/edit/` | Edit |
| `/proposals/<pk>/print/` | Print/PDF |
| `/proposals/<pk>/convert/` | Convert accepted quote to invoice |
