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
