from django.db import models
from django.conf import settings
from leads.models import Lead


class Client(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("at_risk", "At Risk"),
        ("inactive", "Inactive"),
        ("churned", "Churned"),
    ]
    organization_name = models.CharField(max_length=200)
    linked_lead = models.OneToOneField(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="client"
    )
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    tags = models.ManyToManyField('dashboard.Tag', blank=True, related_name='clients')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["organization_name"]

    def __str__(self):
        return self.organization_name


class ClientContact(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "name"]

    def __str__(self):
        return f"{self.name} ({self.client})"


class ClientInteraction(models.Model):
    TYPE_CHOICES = [
        ("call", "Call"),
        ("meeting", "Meeting"),
        ("email", "Email"),
        ("check_in", "Check-in"),
        ("support", "Support"),
        ("renewal", "Renewal Discussion"),
        ("other", "Other"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="interactions")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="call")
    notes = models.TextField()
    next_follow_up_date = models.DateField(null=True, blank=True)
    follow_up_done = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="client_interactions/", blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="client_interactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} – {self.client}"

    @property
    def attachment_is_image(self):
        if not self.attachment:
            return False
        ext = self.attachment.name.rsplit(".", 1)[-1].lower()
        return ext in ("jpg", "jpeg", "png", "gif", "webp")


class ContractTemplate(models.Model):
    BILLING_CYCLE_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]
    name = models.CharField(max_length=200)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default="yearly")
    default_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Terms and conditions pre-filled on new contracts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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
