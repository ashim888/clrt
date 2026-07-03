# Landing Page & Marketing

---

## Entry point routing

The root URL (`/`) is handled by `dashboard.views.dashboard`:

- **Unauthenticated** → renders `templates/landing.html` with GA4 ID from SiteSettings
- **Authenticated** → renders `templates/dashboard/dashboard.html` with full KPI context

No separate URL is needed for the landing page.

---

## Landing page (`templates/landing.html`)

Standalone template — does **not** extend `base.html`. Uses Tailwind CDN and Inter font directly.

### Sections (in order)

| Section | `data-section` | Description |
|---|---|---|
| Nav | — | Sticky, blur backdrop, anchor links, Sign In + Get Access CTA |
| Hero | `hero` | Two-column: headline + trust badges / mini dashboard mockup |
| Stats strip | `stats` | Dark band, 4 animated counters |
| Who it's for | `audience` | 3 persona cards |
| Features | `features` | 6 feature cards with icon chips |
| How it works | `how_it_works` | Dark section, 4 glassmorphism step cards |
| Testimonials | `testimonials` | 3 star-rated quote cards |
| Pricing | `pricing` | 3-tier cards pulled from static HTML (see note below) |
| FAQ | `faq` | `<details>` accordion, no JS needed |
| Get Access | `get_access` | Sign-up form POSTing to `/signup/` |
| Footer | — | 4-column with product + account links |

> **Pricing on the landing page is static HTML.** Dynamic plan data (from the `Plan` model) is shown on the in-app Subscription page (`/subscription/`). Update the landing page pricing manually when plan prices change.

### Template restrictions

The landing page cannot use:
- `{% load clrt_filters %}` — `clrt_filters` is a template builtin only when `base.html` is extended
- Any filter from `clrt_filters` (`inr`, `site_date`)
- Any context variable from context processors (`current_sub`, `current_plan`, `settings`, etc.)

Available context: `ga_id` (string, may be empty).

---

## Get Access form

**Template:** `templates/landing.html` — `#get-access` section  
**Backend:** `dashboard.views.landing_signup`  
**URL:** `/signup/` (POST, `@csrf_exempt`)

The form POSTs JSON:

```json
{
  "name": "Ashim Shrestha",
  "email": "ashim@company.com",
  "company": "TechNova",
  "phone": "+977 98XXXXXXXX",
  "plan": "Growth — Rs. 2,499/month",
  "session": "<session-id>"
}
```

On success the backend:
1. Creates a `Lead` with `source="website"` and the plan interest in `notes`
2. Creates a `PageEvent` with `event="signup_submit"`
3. Returns `{"ok": true}`

The form JS handles the success state inline (hides form, shows `🎉` message) without a page reload.

---

## Contact Sales page

**Template:** `templates/contact.html`  
**View:** `dashboard.views.contact_sales`  
**URL:** `/contact/` (GET + POST)

Standalone page matching the landing page visual style. Form fields:

- Full Name *, Work Email *
- Company Name, Phone/WhatsApp
- Team Size (dropdown), Current tool
- Plan interest (pre-selected to Enterprise), Monthly budget
- Requirements & questions * (textarea)
- How did you hear about us

On POST: saves a `Lead` with `source="website"` and all extra fields concatenated into `notes`. Shows an inline success state — no redirect.

Linked from:
- Landing page pricing section "Contact sales" button (Enterprise tier)
- Landing page footer "Contact us" link

---

## Analytics tracking

### Custom events (`PageEvent` model)

Every visitor interaction is tracked to `dashboard.models.PageEvent`:

| Event | Trigger |
|---|---|
| `page_view` | On load |
| `click` | Any `[data-track]` element clicked |
| `scroll_25/50/75/90` | Scroll depth milestones |
| `section_view` | Any `[data-section]` element enters viewport (IntersectionObserver) |
| `time_on_page` | `visibilitychange` → hidden (via `navigator.sendBeacon`) |
| `signup_submit` | Form submitted to `/signup/` |
| `signup_complete` | `/signup/` returns `{ok: true}` |

Session is stored in `sessionStorage` under key `clrt_sid`. Generated with `crypto.randomUUID()`.

**Endpoint:** `POST /analytics/track/` (`@csrf_exempt`)

Request body (JSON):
```json
{
  "session": "uuid",
  "event": "click",
  "page": "/",
  "referrer": "https://google.com",
  "target": "hero_cta_primary"
}
```

### View analytics

Go to **Analytics** in the sidebar (`/analytics/`) — shows event counts by day (Chart.js bar chart) and a breakdown of event types.

### Google Analytics 4 (optional)

Set `ga_measurement_id` in **SiteSettings** (e.g. `G-XXXXXXXXXX`). The GA4 script is injected in the landing page `{% if ga_id %}` block. `gtag('event', ...)` is also called in parallel with every custom event track, so both systems receive the same data.
