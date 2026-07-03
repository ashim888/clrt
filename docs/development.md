# Development Guide

---

## Conventions

### Views

- All views are **function-based** with `@login_required`
- Permission checks use `request.user.is_admin()`, `request.user.is_accounts()`, etc.
- AJAX endpoints return `JsonResponse({"ok": True})` or `JsonResponse({"error": "..."}, status=4xx)`
- Public endpoints (landing page analytics, lead capture) use `@csrf_exempt @require_POST`
- Feature-gated views use `@requires_feature("has_<feature>")` from `dashboard.decorators`

### Templates

- All app templates extend `{% extends "base.html" %}`
- The landing page (`landing.html`) and contact page (`contact.html`) are **standalone** — they do not extend `base.html` and cannot use `clrt_filters` or context processor variables
- Template builtins: `clrt_filters` is auto-loaded (no `{% load %}` needed) in templates that extend `base.html`
- Tailwind CSS is via CDN — dynamic values (e.g. computed widths) must use `style=""` attributes; avoid Tailwind JIT arbitrary values like `w-[123px]` that won't be in the CDN build

### Models

- All timestamps use `auto_now_add` or `auto_now` on DateTimeFields — always `USE_TZ=True`
- Display datetimes: use `timezone.localtime()` before `.strftime()` — never call strftime on raw UTC datetimes
- Singleton models (`SiteSettings`) enforce `pk=1` in `save()` and use a `load()` classmethod

### URLs

- Named URLs follow `<app_name>:<view_name>` pattern
- All dashboard-level URLs mount at `/` (no prefix) via `include("dashboard.urls")`
- App-level URLs: `/leads/`, `/clients/`, `/billing/`, `/proposals/`, `/catalog/`, `/accounts/`

---

## Adding a new feature

### 1. Model

Add to the appropriate app's `models.py`. Run:

```bash
python manage.py makemigrations <app>
python manage.py migrate
```

### 2. View

```python
@login_required
def my_feature(request):
    # ...
    return render(request, "myapp/my_feature.html", context)
```

### 3. URL

In `myapp/urls.py`:

```python
path("my-feature/", views.my_feature, name="my_feature"),
```

### 4. Template

```html
{% extends "base.html" %}
{% block title %}My Feature{% endblock %}
{% block content %}
  <!-- content here -->
{% endblock %}
```

### 5. Sidebar link (optional)

Add to `templates/base.html` in the appropriate section.

### 6. Feature gate (if plan-restricted)

Add a `has_my_feature` BooleanField to `Plan`, migrate, then:

```python
@requires_feature("has_my_feature")
def my_feature(request):
    ...
```

---

## Template filters (`clrt_filters`)

**File:** `dashboard/templatetags/clrt_filters.py`

Auto-loaded as a builtin — no `{% load %}` needed in templates extending `base.html`.

| Filter | Usage | Description |
|---|---|---|
| `inr` | `{{ amount\|inr }}` | Format number with currency symbol and Indian/Western number format from SiteSettings |
| `site_date` | `{{ date\|site_date }}` | Format date using date_format from SiteSettings |

These filters read from `SiteSettings` with an in-process cache. The cache is cleared whenever `SiteSettings.save()` is called.

---

## Context processors

Injected into every template that uses the Django template engine:

| Processor | Variables injected |
|---|---|
| `dashboard.context_processors.site_settings` | `settings` (SiteSettings object) |
| `dashboard.context_processors.notifications` | `unread_notifications`, `unread_count` |
| `dashboard.context_processors.subscription` | `current_sub`, `current_plan` |

These are **not** available in standalone templates (`landing.html`, `contact.html`).

---

## Notifications

Push an in-app notification from anywhere:

```python
from dashboard.models import Notification

Notification.push(
    user=some_user,          # accounts.User — pass None to skip silently
    title="Something happened",
    body="More details here",
    link="/leads/42/",
    type="lead",             # lead / followup / invoice / contract / system
)
```

Notifications appear in the bell icon in `base.html` via the `notifications` context processor.

---

## Common gotchas

**Logout as GET:** Django 5.x `LogoutView` requires POST. Always use a `<form method="post">` with `{% csrf_token %}`, not an `<a href>` link.

**Inline status change:** The lead list uses `fetch()` to POST to `/leads/<pk>/status/`. If the view needs to redirect (e.g. on won status), return `{"redirect": "/clients/"}` in the JSON and handle it in JS.

**Bulk action bar:** The floating bulk bar on lead/client lists uses CSS hover states for dropdowns (`.group:hover .hidden`). This avoids JS complexity but means dropdowns close the moment the mouse leaves — acceptable UX for a management tool.

**SQLite and concurrent writes:** SQLite has write locks. For personal/single-user use this is fine. For multi-user production, switch to PostgreSQL.

**2FA session:** `request.session['2fa_verified']` is set after a successful TOTP check. Django's `LogoutView` clears the entire session, so 2FA is always required again after logout.
