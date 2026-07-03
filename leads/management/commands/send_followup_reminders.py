from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q


class Command(BaseCommand):
    help = "Send daily follow-up reminders (in-app notifications + optional emails)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Print what would be sent without creating notifications or sending emails",
        )
        parser.add_argument(
            "--no-email", action="store_true",
            help="Create in-app notifications only, skip emails",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        no_email = options["no_email"]
        today = timezone.localdate()

        from leads.models import Activity
        from clients.models import ClientInteraction, Contract
        from billing.models import Invoice
        from dashboard.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()

        sent = 0
        notif_count = 0

        # ── 1. Lead activity follow-ups ─────────────────────────────
        # Activities with next_follow_up_date today or overdue, not yet completed/cancelled
        lead_activities = (
            Activity.objects
            .filter(
                next_follow_up_date__isnull=False,
                next_follow_up_date__lte=today,
                status__in=["pending", "rescheduled"],
            )
            .select_related("lead", "lead__assigned_to", "created_by")
        )

        # Group by the responsible user: lead.assigned_to, fallback to created_by
        user_lead_map = {}
        for act in lead_activities:
            user = act.lead.assigned_to or act.created_by
            if user:
                user_lead_map.setdefault(user, []).append(act)

        for user, activities in user_lead_map.items():
            overdue = [a for a in activities if a.next_follow_up_date < today]
            due_today = [a for a in activities if a.next_follow_up_date == today]

            title = f"{len(activities)} lead follow-up(s) due"
            if overdue:
                title = f"{len(overdue)} overdue + {len(due_today)} due today — leads"

            body_lines = []
            for act in sorted(activities, key=lambda a: a.next_follow_up_date):
                tag = "OVERDUE" if act.next_follow_up_date < today else "TODAY"
                body_lines.append(
                    f"[{tag}] {act.lead.organization_name} — "
                    f"{act.get_type_display()} (due {act.next_follow_up_date})"
                )

            self.stdout.write(f"  Lead reminders → {user.username}: {len(activities)} item(s)")

            if not dry_run:
                Notification.push(
                    user=user,
                    title=title,
                    body="; ".join(body_lines[:3]) + ("…" if len(body_lines) > 3 else ""),
                    link="/leads/",
                    type="followup",
                )
                notif_count += 1

                if not no_email and user.email and _email_configured():
                    email_body = (
                        f"Hi {user.get_full_name() or user.username},\n\n"
                        f"You have {len(activities)} lead follow-up(s) pending:\n\n"
                        + "\n".join(f"  • {l}" for l in body_lines)
                        + "\n\nLog in to CLRT to take action: "
                        + getattr(settings, "SITE_URL", "http://localhost:8000")
                        + "/leads/"
                    )
                    send_mail(
                        subject=f"[CLRT] {title}",
                        message=email_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                    sent += 1
                    self.stdout.write(f"    → Email sent to {user.email}")

        # ── 2. Client interaction follow-ups ─────────────────────────
        client_followups = (
            ClientInteraction.objects
            .filter(next_follow_up_date__lte=today, follow_up_done=False)
            .select_related("client", "created_by")
        )

        user_client_map = {}
        for ci in client_followups:
            user = ci.created_by
            if user:
                user_client_map.setdefault(user, []).append(ci)

        for user, interactions in user_client_map.items():
            title = f"{len(interactions)} client follow-up(s) due"
            body_lines = [
                f"{ci.client.organization_name} — {ci.get_type_display()} (due {ci.next_follow_up_date})"
                for ci in sorted(interactions, key=lambda c: c.next_follow_up_date)
            ]
            self.stdout.write(f"  Client reminders → {user.username}: {len(interactions)} item(s)")

            if not dry_run:
                Notification.push(
                    user=user,
                    title=title,
                    body="; ".join(body_lines[:3]) + ("…" if len(body_lines) > 3 else ""),
                    link="/clients/",
                    type="followup",
                )
                notif_count += 1

                if not no_email and user.email and _email_configured():
                    email_body = (
                        f"Hi {user.get_full_name() or user.username},\n\n"
                        f"You have {len(interactions)} client follow-up(s) pending:\n\n"
                        + "\n".join(f"  • {l}" for l in body_lines)
                        + "\n\nLog in to CLRT: "
                        + getattr(settings, "SITE_URL", "http://localhost:8000")
                        + "/clients/"
                    )
                    send_mail(
                        subject=f"[CLRT] {title}",
                        message=email_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                    sent += 1

        # ── 3. Expiring contracts (within 30 days) ────────────────────
        soon = today + timezone.timedelta(days=30)
        expiring = (
            Contract.objects
            .filter(end_date__gte=today, end_date__lte=soon, status="active")
            .select_related("client")
            .order_by("end_date")
        )

        if expiring.exists():
            lines = [
                f"{c.client.organization_name} — expires {c.end_date} ({(c.end_date - today).days}d)"
                for c in expiring
            ]
            self.stdout.write(f"  Expiring contracts: {expiring.count()}")

            # Notify all admins
            admins = User.objects.filter(Q(role="admin") | Q(is_superuser=True), is_active=True)
            for admin in admins:
                if not dry_run:
                    Notification.push(
                        user=admin,
                        title=f"{expiring.count()} contract(s) expiring within 30 days",
                        body="; ".join(lines[:3]) + ("…" if len(lines) > 3 else ""),
                        link="/clients/",
                        type="contract",
                    )
                    notif_count += 1

            admin_email = getattr(settings, "ADMIN_EMAIL", "")
            if not dry_run and not no_email and admin_email and _email_configured():
                body = (
                    "Contracts expiring within 30 days:\n\n"
                    + "\n".join(f"  • {l}" for l in lines)
                    + "\n\nLog in to review: "
                    + getattr(settings, "SITE_URL", "http://localhost:8000")
                    + "/clients/"
                )
                send_mail(
                    subject=f"[CLRT] {expiring.count()} contract(s) expiring soon",
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=True,
                )
                sent += 1

        # ── 4. Overdue invoices digest ────────────────────────────────
        overdue_inv = (
            Invoice.objects
            .filter(status="overdue")
            .select_related("client")
            .order_by("due_date")
        )

        if overdue_inv.exists():
            lines = [
                f"{inv.client.organization_name} — {inv.invoice_number} ({inv.amount_due} overdue)"
                for inv in overdue_inv
            ]
            self.stdout.write(f"  Overdue invoices: {overdue_inv.count()}")

            admins = User.objects.filter(Q(role="admin") | Q(is_superuser=True), is_active=True)
            for admin in admins:
                if not dry_run:
                    Notification.push(
                        user=admin,
                        title=f"{overdue_inv.count()} overdue invoice(s) need attention",
                        body="; ".join(lines[:3]) + ("…" if len(lines) > 3 else ""),
                        link="/billing/",
                        type="invoice",
                    )
                    notif_count += 1

            admin_email = getattr(settings, "ADMIN_EMAIL", "")
            if not dry_run and not no_email and admin_email and _email_configured():
                body = (
                    "Overdue invoices:\n\n"
                    + "\n".join(f"  • {l}" for l in lines)
                    + "\n\nLog in to follow up: "
                    + getattr(settings, "SITE_URL", "http://localhost:8000")
                    + "/billing/"
                )
                send_mail(
                    subject=f"[CLRT] {overdue_inv.count()} overdue invoice(s)",
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=True,
                )
                sent += 1

        # ── Summary ───────────────────────────────────────────────────
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Done — {notif_count} notification(s) created, {sent} email(s) sent."
        ))


def _email_configured():
    """Return True only if a real email backend is configured (not console/file/memory)."""
    backend = getattr(settings, "EMAIL_BACKEND", "")
    return "console" not in backend and "file" not in backend and "memory" not in backend
