# Plans, Subscriptions & Feature Gating

---

## Models

### `Plan` (`dashboard.models`)

| Field | Type | Notes |
|---|---|---|
| `name` | CharField | Display name (Starter / Growth / Enterprise) |
| `slug` | CharField | `starter` / `growth` / `enterprise` — unique |
| `tagline` | CharField | Short description shown on pricing page |
| `price_monthly` | Decimal | Monthly price in local currency |
| `price_yearly` | Decimal | Annual price (typically 10 × monthly) |
| `is_active` | Boolean | Inactive plans are hidden from pricing page |
| `max_leads` | PositiveInt | Hard limit on leads; **0 = unlimited** |
| `max_clients` | PositiveInt | Hard limit on clients; **0 = unlimited** |
| `max_users` | PositiveInt | Hard limit on team members; **0 = unlimited** |
| `max_invoices` | PositiveInt | Hard limit on invoices; **0 = unlimited** |
| `has_reports` | Boolean | Reports & Analytics page |
| `has_proposals` | Boolean | Quotes & Proposals |
| `has_razorpay` | Boolean | Razorpay payment gateway |
| `has_client_portal` | Boolean | Client self-service portal |
| `has_web_capture` | Boolean | Embeddable lead capture form |
| `has_quota_tracking` | Boolean | Revenue quota / goal tracking |
| `has_audit_log` | Boolean | Audit trail page |
| `has_calendar` | Boolean | Calendar & events (default: True) |
| `has_catalog` | Boolean | Product/service catalog |
| `has_custom_branding` | Boolean | Custom branding on portal & documents |
| `custom_features` | JSONField (list) | Feature strings shown on the in-app pricing/subscription page. Edit via admin. |

### `Subscription` (`dashboard.models`)

One active subscription at a time (singleton pattern via `Subscription.current()`).

| Field | Notes |
|---|---|
| `plan` | FK to Plan |
| `status` | `trialing` / `active` / `past_due` / `cancelled` / `expired` |
| `trial_ends` | Date — if set and past, status auto-expires to `expired` on next `current()` call |
| `period_start / period_end` | Billing period dates |
| `notes` | Admin notes |

#### `Subscription.current()`

```python
sub = Subscription.current()
```

Returns the current active/trialing subscription, or `None`. Automatically marks expired trials.

---

## Feature gating

### `requires_feature` decorator

**File:** `dashboard/decorators.py`

Wrap any view to gate it behind a plan feature flag:

```python
from dashboard.decorators import requires_feature

@requires_feature("has_reports")
def reports(request):
    ...
```

If the current subscription doesn't have the feature, the user sees `templates/dashboard/upgrade_required.html` instead of the view.

### `check_limit` helper

```python
from dashboard.decorators import check_limit
from leads.models import Lead

if not check_limit(Lead, "max_leads"):
    # plan limit reached
    messages.error(request, "Lead limit reached for your plan.")
    return redirect("leads:lead_list")
```

Returns `True` if usage is under the plan limit (0 = unlimited always returns `True`).

### Context processors

`dashboard.context_processors.subscription` injects into every template:

```
{{ current_sub }}   — current Subscription object or None
{{ current_plan }}  — current Plan object or None
```

Use these in templates to conditionally show upgrade prompts:

```html
{% if not current_plan.has_reports %}
<a href="{% url 'dashboard:subscription' %}">Upgrade to access reports</a>
{% endif %}
```

---

## Managing plans

### Via Django Admin

`/admin/dashboard/plan/` — edit all plan fields including `custom_features` (JSON list of strings).

### Via shell

```python
from dashboard.models import Plan
p = Plan.objects.get(slug="growth")
p.custom_features = ["New feature string", "Another feature"]
p.save()
```

### Creating a subscription

```python
from dashboard.models import Plan, Subscription
from django.utils import timezone

plan = Plan.objects.get(slug="growth")
Subscription.objects.create(
    plan=plan,
    status="trialing",
    trial_ends=timezone.now().date() + timezone.timedelta(days=30),
)
```

---

## Subscription page (in-app)

**URL:** `/subscription/`  
**Template:** `templates/dashboard/subscription.html`

Shows:
- Current plan status banner (trial days remaining, active/expired)
- 3-column plan comparison grid
- Features pulled from `Plan.custom_features` (JSONField list of strings)
- Hard limits (leads / clients / users / invoices) auto-rendered from model fields
- Upgrade / Contact Sales buttons

---

## Upgrade wall

**Template:** `templates/dashboard/upgrade_required.html`

Shown automatically by the `requires_feature` decorator. Displays:
- Which feature is locked
- Current plan name
- Link to `/subscription/` to compare plans

---

## Adding a new feature flag

1. Add a `has_<feature>` BooleanField to `Plan` in `dashboard/models.py`
2. Run `python manage.py makemigrations dashboard && python manage.py migrate`
3. Update existing plans in admin (set True/False as appropriate)
4. Wrap the gated view: `@requires_feature("has_<feature>")`
5. Update `Plan.custom_features` strings for each plan via admin
