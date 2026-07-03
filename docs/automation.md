# Automation & Reminders

---

## Follow-up reminder command

**File:** `leads/management/commands/send_followup_reminders.py`

Run daily to:
1. Create in-app notifications for pending lead activity follow-ups
2. Create in-app notifications for pending client interaction follow-ups
3. Notify all admins about contracts expiring within 30 days
4. Notify all admins about overdue invoices
5. Send emails for all of the above (only when a real SMTP backend is configured)

### Run manually

```bash
source venv/bin/activate
python manage.py send_followup_reminders
```

### Flags

| Flag | Effect |
|---|---|
| `--dry-run` | Print what would be sent; no notifications created, no emails sent |
| `--no-email` | Create in-app notifications only; skip all email sending |

```bash
# Test without side effects
python manage.py send_followup_reminders --dry-run

# In-app notifications only (useful in staging)
python manage.py send_followup_reminders --no-email
```

### What it checks

| Check | Criteria | Notifies |
|---|---|---|
| Lead follow-ups | `Activity.next_follow_up_date <= today` AND `status` in `pending/rescheduled` | `lead.assigned_to`, fallback to `activity.created_by` |
| Client follow-ups | `ClientInteraction.next_follow_up_date <= today` AND `follow_up_done=False` | `interaction.created_by` |
| Expiring contracts | `Contract.end_date` within 30 days AND `status=active` | All admin users + `ADMIN_EMAIL` |
| Overdue invoices | `Invoice.status = overdue` | All admin users + `ADMIN_EMAIL` |

### Email vs notification

In-app `Notification` objects are **always** created (they appear in the notification bell in the top bar).

Emails are sent only when:
- `EMAIL_BACKEND` is **not** `console`, `file`, or `memory` backend
- The recipient has a non-empty `email` field

Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` and the SMTP variables in `.env` to enable real emails. See [configuration.md](configuration.md).

---

## Cron setup

Run the command every morning at 8:00 AM server time.

### Linux / macOS crontab

```bash
crontab -e
```

Add:

```cron
0 8 * * * cd /path/to/clrt && /path/to/clrt/venv/bin/python manage.py send_followup_reminders >> /var/log/clrt_reminders.log 2>&1
```

Replace `/path/to/clrt` with your actual project path.

### Verify the path

```bash
which python   # inside venv: /path/to/clrt/venv/bin/python
pwd            # should be /path/to/clrt
```

### Systemd timer (alternative)

Create `/etc/systemd/system/clrt-reminders.service`:

```ini
[Unit]
Description=CLRT daily follow-up reminders

[Service]
Type=oneshot
WorkingDirectory=/path/to/clrt
ExecStart=/path/to/clrt/venv/bin/python manage.py send_followup_reminders
```

Create `/etc/systemd/system/clrt-reminders.timer`:

```ini
[Unit]
Description=Run CLRT reminders daily at 08:00

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
systemctl enable clrt-reminders.timer
systemctl start clrt-reminders.timer
```

---

## Adding a new management command

1. Create `<app>/management/__init__.py` and `<app>/management/commands/__init__.py` if they don't exist
2. Create `<app>/management/commands/<command_name>.py`:

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Description of what this does"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        # your logic here
        self.stdout.write(self.style.SUCCESS("Done."))
```

3. Run with: `python manage.py <command_name>`
