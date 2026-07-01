from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from leads.models import Activity
from clients.models import ClientInteraction
from billing.models import Contract


class Command(BaseCommand):
    help = "Send daily follow-up reminder emails to assigned users"

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent = 0

        # Lead activity follow-ups (pending or rescheduled, due today or overdue)
        lead_followups = (
            Activity.objects
            .filter(
                Q(status="pending") | Q(status="rescheduled"),
                Q(next_follow_up_date__lte=today) | Q(scheduled_date__date__lte=today),
            )
            .select_related("lead", "assigned_to")
        )
        # Group by user
        user_lead_map = {}
        for act in lead_followups:
            user = act.assigned_to or getattr(act.lead, "assigned_to", None)
            if user and user.email:
                user_lead_map.setdefault(user, []).append(act)

        for user, activities in user_lead_map.items():
            lines = []
            for act in activities:
                lines.append(f"  • {act.lead.organization_name} — {act.type} (due {act.next_follow_up_date or act.scheduled_date})")
            body = (
                f"Hi {user.get_full_name() or user.username},\n\n"
                f"You have {len(activities)} lead follow-up(s) due today or overdue:\n\n"
                + "\n".join(lines)
                + "\n\nLog in to CLRT to take action."
            )
            send_mail(
                subject=f"[CLRT] {len(activities)} lead follow-up(s) pending",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            sent += 1
            self.stdout.write(f"  Sent lead reminder to {user.email} ({len(activities)} items)")

        # Client interaction follow-ups due today or overdue
        client_followups = (
            ClientInteraction.objects
            .filter(next_follow_up_date__lte=today, follow_up_done=False)
            .select_related("client", "created_by")
        )
        user_client_map = {}
        for ci in client_followups:
            user = ci.created_by
            if user and user.email:
                user_client_map.setdefault(user, []).append(ci)

        for user, interactions in user_client_map.items():
            lines = []
            for ci in interactions:
                lines.append(f"  • {ci.client.organization_name} — {ci.get_type_display()} (due {ci.next_follow_up_date})")
            body = (
                f"Hi {user.get_full_name() or user.username},\n\n"
                f"You have {len(interactions)} client follow-up(s) due today or overdue:\n\n"
                + "\n".join(lines)
                + "\n\nLog in to CLRT to mark them done."
            )
            send_mail(
                subject=f"[CLRT] {len(interactions)} client follow-up(s) pending",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            sent += 1
            self.stdout.write(f"  Sent client reminder to {user.email} ({len(interactions)} items)")

        # Expiring contracts (within 30 days)
        soon = today + timezone.timedelta(days=30)
        expiring = (
            Contract.objects
            .filter(end_date__gte=today, end_date__lte=soon, status="active")
            .select_related("client")
        )
        if expiring.exists() and settings.ADMIN_EMAIL:
            lines = [f"  • {c.client.organization_name} — expires {c.end_date}" for c in expiring]
            body = (
                f"These contracts expire within 30 days:\n\n"
                + "\n".join(lines)
                + "\n\nLog in to CLRT to review."
            )
            send_mail(
                subject=f"[CLRT] {expiring.count()} contract(s) expiring soon",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
            sent += 1
            self.stdout.write(f"  Sent contract expiry digest to {settings.ADMIN_EMAIL}")

        # Overdue invoices digest
        from billing.models import Invoice
        overdue = Invoice.objects.filter(status="overdue").select_related("client")
        if overdue.exists() and settings.ADMIN_EMAIL:
            lines = [f"  • {inv.client.organization_name} — {inv.invoice_number} (Rs. {inv.amount_due})" for inv in overdue]
            body = (
                f"These invoices are overdue:\n\n"
                + "\n".join(lines)
                + "\n\nLog in to CLRT to follow up."
            )
            send_mail(
                subject=f"[CLRT] {overdue.count()} overdue invoice(s)",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
            sent += 1
            self.stdout.write(f"  Sent overdue invoice digest to {settings.ADMIN_EMAIL}")

        self.stdout.write(self.style.SUCCESS(f"Done — {sent} email(s) sent."))
