"""
Management command: python manage.py check_alerts
Mimics the daily scheduler - marks overdue invoices, prints alerts.
Run this via cron: 0 9 * * * /path/to/venv/python manage.py check_alerts
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from leads.models import Activity
from clients.models import Contract
from billing.models import Invoice


class Command(BaseCommand):
    help = "Check and print daily alerts: follow-ups, expiring contracts, overdue invoices"

    def handle(self, *args, **options):
        today = timezone.now().date()

        # Mark overdue invoices
        updated = Invoice.objects.filter(status="pending", due_date__lt=today).update(status="overdue")
        self.stdout.write(f"[BILLING] Marked {updated} invoice(s) as overdue.")

        # Follow-ups due today
        followups = Activity.objects.filter(next_follow_up_date=today)
        self.stdout.write(f"[FOLLOWUP] {followups.count()} follow-up(s) due today.")
        for f in followups:
            self.stdout.write(f"  - {f.lead.organization_name} ({f.get_type_display()})")

        # Contracts expiring in 30 days
        in_30 = today + timezone.timedelta(days=30)
        contracts = Contract.objects.filter(status="active", end_date__gte=today, end_date__lte=in_30)
        self.stdout.write(f"[CONTRACTS] {contracts.count()} contract(s) expiring within 30 days.")
        for c in contracts:
            self.stdout.write(f"  - {c.client} | {c.contract_title} | expires {c.end_date}")
