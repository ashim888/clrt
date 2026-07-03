# Billing & Invoicing

---

## Invoice model (`billing.models.Invoice`)

| Field | Notes |
|---|---|
| `client` | FK to `clients.Client` |
| `invoice_number` | Auto-generated: `{prefix}-{YYYY}-{N}` e.g. `INV-2025-001` |
| `generated_date` | Date invoice was created |
| `due_date` | Payment due date |
| `amount` | Total invoice amount |
| `amount_due` | Outstanding amount (after partial payments) |
| `status` | `pending / paid / overdue / cancelled` |
| `notes` | Internal notes |
| `payment_terms` | Terms text printed on invoice (defaults from SiteSettings) |
| `razorpay_order_id` | Set when Razorpay payment link is generated |
| `razorpay_payment_id` | Set on successful Razorpay payment |

---

## Invoice numbering

Invoice numbers auto-increment per year. Format:

```
{invoice_prefix}-{YYYY}-{NNN}
```

`invoice_prefix` is set in **SiteSettings** (default: `INV`). The counter resets at the start of each calendar year.

---

## Invoice statuses

| Status | Meaning |
|---|---|
| `pending` | Issued but not yet paid |
| `paid` | Fully paid |
| `overdue` | Past due date and not paid — set manually or via the overdue check |
| `cancelled` | Voided |

Mark invoices overdue manually from the invoice detail page, or run the `send_followup_reminders` command which alerts admins to overdue invoices.

---

## Online payments (Razorpay)

**Requires:** Growth or Enterprise plan (`has_razorpay=True`)

### Setup

1. Create a Razorpay account at [razorpay.com](https://razorpay.com)
2. Get your Key ID and Key Secret from the Razorpay dashboard
3. In CLRT **Settings** (`/settings/`), fill in:
   - Razorpay Key ID
   - Razorpay Key Secret
   - Toggle **Razorpay Enabled** to On

### How it works

On the invoice detail page, when Razorpay is enabled, a **Pay Online** button appears. Clicking it:

1. Creates a Razorpay order via the API and stores `razorpay_order_id` on the invoice
2. Opens the Razorpay checkout modal
3. On successful payment, stores `razorpay_payment_id` and sets `invoice.status = "paid"`

The client portal also shows **Pay Online** for pending invoices when Razorpay is enabled.

---

## Print / PDF

Invoice detail page has a **Print** button (`/billing/<pk>/print/`) which renders a clean printable layout at `templates/billing/invoice_print.html`. Use the browser's **Print to PDF** option.

---

## URLs (`billing` app)

| URL | Description |
|---|---|
| `/billing/` | Invoice list |
| `/billing/add/` | Create invoice |
| `/billing/<pk>/` | Invoice detail |
| `/billing/<pk>/edit/` | Edit invoice |
| `/billing/<pk>/print/` | Print/PDF view |
| `/billing/<pk>/mark-paid/` | Mark as paid (POST) |
| `/billing/<pk>/razorpay/` | Initiate Razorpay payment |
| `/billing/razorpay/callback/` | Razorpay webhook/callback |
