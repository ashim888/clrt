# Reports & Analytics

---

## Overview page (`/reports/`)

The main reports view. Supports an optional **date range filter** (from/to dates) applied to leads created and invoices generated within the range.

### KPI sections

**Revenue & Billing**

| Metric | Source |
|---|---|
| Total Collected | Sum of paid invoice amounts in period |
| Outstanding | Sum of pending + overdue invoice amounts (always all-time) |
| Active Clients | Count of clients with `status=active` |
| Conversion Rate | `won_leads / total_leads × 100` |

**Pipeline Value**

| Metric | Calculation |
|---|---|
| Active Pipeline | Sum of `deal_value` for leads in New / Contacted / Demo / Negotiation |
| Weighted Forecast | Sum of `deal_value × stage_probability` for active leads |
| Won Deals Value | Sum of `deal_value` for won leads |

Stage probability weights: New 10%, Contacted 25%, Demo 50%, Negotiation 75%.

**Sales Velocity**

| Metric | Calculation |
|---|---|
| Avg. Days to Close | Average `updated_at − created_at` for won leads (proxy for close date) |
| Avg. First Touch | Average days from lead creation to first logged activity |
| Overall Win Rate | Same as Conversion Rate |
| Lost Leads | Count + percentage of total |

### Charts

| Chart | Type | Description |
|---|---|---|
| Monthly Revenue | Bar | Paid invoice totals by month, last 12 months (or date range) |
| Lead Pipeline | Bar | Count of leads at each stage |
| Pipeline Value | Bar | Deal value at each stage |
| Lead Sources | Doughnut | Count of leads by source |
| Client Health | Doughnut | Clients by status (active/at_risk/inactive/churned) |

### Conversion funnel

Visual bar chart showing leads currently at each stage (New → Contacted → Demo → Negotiation → Won) with drop-off percentage between stages.

> Note: this is a **cross-sectional** view (leads currently at each stage), not a true cohort funnel (which would require tracking historical status changes).

### Source performance table

For each lead source that has leads: shows total / won / lost / active counts and **win rate %** as a colour-coded progress bar. Sorted by win rate descending. Green ≥50%, amber ≥25%, red below 25%.

### Lost reasons

Bar chart of the most common `lost_reason` values, ranked by frequency. Reasons are captured when marking a lead as lost (modal prompt on status change).

---

## Sub-reports

| URL | Description |
|---|---|
| `/reports/leads/` | Detailed lead report with date range, source filter, assignment filter |
| `/reports/clients/` | Client report: billed, collected, outstanding per client |
| `/reports/billing/` | Invoice report: totals by status and month |
| `/reports/team/` | Team performance: activities and won deals per user |

---

## Analytics dashboard (`/analytics/`)

Built-in visitor analytics for the **landing page**.

Shows:
- Events per day (bar chart, last 30 days)
- Total events by type (table)

Data source: `dashboard.models.PageEvent` — populated by the analytics tracking JS on the landing page and by the `/analytics/track/` endpoint.

**Requires login.** Admin / sales access.

---

## Adding metrics to the reports view

The reports view is in `dashboard/views.py` → `def reports(request)`. Add new querysets and pass them in the context dict. Reference them in `templates/dashboard/reports.html`.

Keep all date-range filtering consistent — apply `date_from` / `date_to` filters to any new querysets that should respect the date filter form.
