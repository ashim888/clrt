# Calendar

---

## Overview

Google Calendar-style event management. Accessible from the dashboard **Calendar** quick-action button or the sidebar.

**URL:** `/calendar/`  
**Requires:** `has_calendar=True` on the current plan (default: True for all plans)

---

## Model (`dashboard.models.CalendarEvent`)

| Field | Notes |
|---|---|
| `title` | Event title |
| `start` | DateTimeField — stored as UTC, displayed in `settings.TIME_ZONE` |
| `end` | DateTimeField (optional) |
| `all_day` | Boolean — if True, only the date portion is used |
| `description` | Free text notes |
| `color` | Hex color string (one of 9 preset swatches) |
| `created_by` | FK to User |

---

## API endpoints

| URL | Method | Description |
|---|---|---|
| `/calendar/` | GET | Render calendar page |
| `/calendar/events/` | GET | Return events as JSON for FullCalendar (supports `start`/`end` query params) |
| `/calendar/events/save/` | POST | Create or update a CalendarEvent |
| `/calendar/events/<pk>/delete/` | POST | Delete a CalendarEvent |

### `GET /calendar/events/`

Returns FullCalendar-compatible JSON. Query params:

| Param | Format | Description |
|---|---|---|
| `start` | `YYYY-MM-DD` | Range start (inclusive) |
| `end` | `YYYY-MM-DD` | Range end (exclusive) |

Events from leads (follow-up dates) and client interactions are also included as read-only entries (`extendedProps.type = "lead"` or `"client"`). Clicking these navigates to the lead/client detail page.

### `POST /calendar/events/save/`

JSON body:

```json
{
  "pk": null,
  "title": "Call with TechNova",
  "start": "2026-07-10",
  "end": null,
  "all_day": true,
  "description": "Discuss renewal",
  "color": "#6366f1"
}
```

Set `pk` to the event ID to update an existing event. Returns `{"ok": true, "pk": N}`.

### `POST /calendar/events/<pk>/delete/`

No body required. Returns `{"ok": true}`.

---

## Timezone handling

All DateTimeFields store UTC. The `calendar_events` view converts to local time before returning to FullCalendar:

```python
from django.utils import timezone as _tz
local_start = _tz.localtime(event.start)
```

For all-day events, only the date string (`YYYY-MM-DD`) is returned. For timed events, the full ISO string including timezone offset is returned so FullCalendar displays correctly.

Range filter queries use `make_aware()` to compare correctly:

```python
from django.utils.timezone import make_aware
from datetime import datetime, time, date
start_aware = make_aware(datetime.combine(date.fromisoformat(start[:10]), time.min))
```

---

## Frontend (FullCalendar.js 6.1)

Key config:

```javascript
selectable: true      // click-drag to select a range → opens create modal
selectMirror: true    // shows placeholder while dragging
dateClick: ...        // click empty date → opens create modal with that date
eventClick: ...       // click custom event → opens edit modal; lead/client events → navigate
```

**Keyboard shortcuts:**
- `Escape` — close modal
- `Ctrl+Enter` / `Cmd+Enter` — save event

**Color swatches:** 9 presets (Indigo, Blue, Green, Amber, Red, Purple, Cyan, Orange, Pink)
