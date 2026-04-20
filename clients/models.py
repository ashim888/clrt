from django.db import models
from leads.models import Lead


class Client(models.Model):
    organization_name = models.CharField(max_length=200)
    linked_lead = models.OneToOneField(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="client"
    )
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["organization_name"]

    def __str__(self):
        return self.organization_name


class Contract(models.Model):
    BILLING_CYCLE_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contracts")
    contract_title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default="yearly")
    contract_value = models.DecimalField(max_digits=12, decimal_places=2)
    document = models.FileField(upload_to="contracts/%Y/%m/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contract_title} - {self.client}"

    @property
    def days_until_expiry(self):
        from django.utils import timezone
        delta = self.end_date - timezone.now().date()
        return delta.days

    @property
    def is_expiring_soon(self):
        return 0 <= self.days_until_expiry <= 30
