# Product & Service Catalog

---

## Overview

A reusable catalog of products and services that can be inserted into invoices and quotes as line items.

**Requires:** `has_catalog=True` on the current plan (Growth / Enterprise)

**URL prefix:** `/catalog/`

---

## Model

Each catalog item stores:
- `name` — product/service name
- `description` — full description
- `unit_price` — standard price
- `unit` — unit label (e.g. "per hour", "per month", "piece")
- `category` — optional grouping
- `is_active` — inactive items are hidden from selection

---

## Usage

When creating an invoice or quote, catalog items appear in a searchable dropdown for line items. Selecting a catalog item pre-fills the description and unit price — both are editable on the invoice/quote.

---

## Managing the catalog

`/catalog/` — list view (requires `has_catalog` plan feature)

Accessible to admin and accounts roles. Add, edit, or deactivate items here.
