from django.db import models
from django.conf import settings
from django.utils import timezone


class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("demo", "Demo"),
        ("negotiation", "Negotiation"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]
    organization_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="leads"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization_name} ({self.get_status_display()})"

    @property
    def is_won(self):
        return self.status == "won"

    @property
    def latest_activity(self):
        return self.activities.order_by("-created_at").first()

    @property
    def next_followup(self):
        return self.activities.filter(
            next_follow_up_date__isnull=False,
            next_follow_up_date__gte=timezone.now().date()
        ).order_by("next_follow_up_date").first()


class Activity(models.Model):
    TYPE_CHOICES = [
        ("call", "Call"),
        ("meeting", "Meeting"),
        ("follow_up", "Follow-up"),
        ("email", "Email"),
    ]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="call")
    notes = models.TextField()
    next_follow_up_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="activities"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} on {self.lead} - {self.created_at.date()}"
