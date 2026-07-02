from django.db import models
from clients.models import Client, Contract


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    generated_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-generated_date"]

    def __str__(self):
        return f"INV-{self.invoice_number} | {self.client} | {self.amount}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.status == "pending" and self.due_date < timezone.now().date()

    def save(self, *args, **kwargs):
        if self.is_overdue and self.status == "pending":
            self.status = "overdue"
        super().save(*args, **kwargs)


class RecurringInvoice(models.Model):
    RECURRENCE_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="recurring_invoices")
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default="monthly")
    day_of_month = models.PositiveSmallIntegerField(default=1, help_text="Day of month to generate invoice (1–28)")
    payment_due_days = models.PositiveSmallIntegerField(default=30, help_text="Days until invoice is due")
    next_date = models.DateField(help_text="Next generation date")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["next_date"]

    def __str__(self):
        return f"{self.client} — {self.get_recurrence_display()} {self.amount}"

    def advance_next_date(self):
        import calendar
        months_delta = {"monthly": 1, "quarterly": 3, "yearly": 12}[self.recurrence]
        y, m = self.next_date.year, self.next_date.month
        m += months_delta
        y += (m - 1) // 12
        m = (m - 1) % 12 + 1
        max_day = calendar.monthrange(y, m)[1]
        day = min(self.day_of_month, max_day, 28)
        from datetime import date as _date
        self.next_date = _date(y, m, day)
        self.save(update_fields=["next_date"])


class Payment(models.Model):
    MODE_CHOICES = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("cheque", "Cheque"),
        ("online", "Online"),
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="bank_transfer")
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount_paid} for {self.invoice}"
