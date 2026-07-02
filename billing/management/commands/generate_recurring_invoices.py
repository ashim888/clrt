from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Generate invoices for all active recurring schedules due today or earlier"

    def handle(self, *args, **options):
        from billing.models import RecurringInvoice, Invoice
        from dashboard.models import SiteSettings

        today = timezone.now().date()
        settings = SiteSettings.load()
        prefix = settings.invoice_prefix or "INV"
        due_schedules = RecurringInvoice.objects.filter(is_active=True, next_date__lte=today).select_related("client")
        created = 0

        for schedule in due_schedules:
            last = (
                Invoice.objects
                .filter(invoice_number__startswith=prefix)
                .order_by("-id")
                .values_list("invoice_number", flat=True)
                .first()
            )
            try:
                seq = int(last.replace(prefix, "").lstrip("-").lstrip("0") or "0") + 1 if last else 1
            except (ValueError, AttributeError):
                seq = Invoice.objects.count() + 1

            inv_number = f"{prefix}-{seq:04d}"
            due_date = schedule.next_date + timedelta(days=schedule.payment_due_days)
            Invoice.objects.create(
                client=schedule.client,
                invoice_number=inv_number,
                amount=schedule.amount,
                due_date=due_date,
                description=schedule.description or f"Recurring invoice — {schedule.get_recurrence_display()}",
                status="pending",
            )
            schedule.advance_next_date()
            created += 1
            self.stdout.write(f"  Created {inv_number} for {schedule.client} (next: {schedule.next_date})")

        self.stdout.write(self.style.SUCCESS(f"Done — {created} invoice(s) generated."))
