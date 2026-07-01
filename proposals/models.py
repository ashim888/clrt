from django.db import models
from django.conf import settings
from django.utils import timezone


class Quote(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("expired", "Expired"),
    ]
    lead = models.ForeignKey(
        "leads.Lead", on_delete=models.CASCADE, related_name="quotes",
        null=True, blank=True,
    )
    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="quotes",
        null=True, blank=True,
    )
    quote_number = models.CharField(max_length=50, unique=True, blank=True)
    title = models.CharField(max_length=200)
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="quotes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.quote_number} – {self.title}"

    @property
    def total(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def recipient_name(self):
        if self.lead:
            return self.lead.organization_name
        if self.client:
            return self.client.organization_name
        return "—"

    @property
    def is_expired(self):
        return self.status not in ("accepted", "declined") and self.valid_until < timezone.now().date()

    def save(self, *args, **kwargs):
        if not self.quote_number:
            super().save(*args, **kwargs)
            year = self.created_at.year
            self.quote_number = f"Q-{year}-{self.pk:04d}"
            Quote.objects.filter(pk=self.pk).update(quote_number=self.quote_number)
        else:
            super().save(*args, **kwargs)


class QuoteLineItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return self.description

    @property
    def line_total(self):
        return self.quantity * self.unit_price
