from django.conf import settings
from django.db import models


class SiteSettings(models.Model):
    CURRENCY_CHOICES = [
        ('Rs.', 'Rs. (Rupee — text)'),
        ('₹', '₹ (Indian Rupee symbol)'),
        ('NPR', 'NPR (Nepalese Rupee)'),
        ('$', '$ (US Dollar)'),
        ('£', '£ (British Pound)'),
        ('€', '€ (Euro)'),
        ('¥', '¥ (Yen / Yuan)'),
    ]
    NUMBER_FORMAT_CHOICES = [
        ('indian', 'Indian  —  1,50,000'),
        ('western', 'Western  —  150,000'),
    ]
    DATE_FORMAT_CHOICES = [
        ('j M Y', 'D Mon YYYY  — 27 Jun 2025'),
        ('d/m/Y', 'DD/MM/YYYY  — 27/06/2025'),
        ('m/d/Y', 'MM/DD/YYYY  — 06/27/2025'),
        ('Y-m-d', 'YYYY-MM-DD  — 2025-06-27'),
        ('j F Y', 'D Month YYYY  — 27 June 2025'),
    ]
    MONTH_CHOICES = [(i, m) for i, m in enumerate(
        ['January', 'February', 'March', 'April', 'May', 'June',
         'July', 'August', 'September', 'October', 'November', 'December'], 1)]

    # — Currency & Numbers —
    currency_symbol = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='Rs.')
    number_format = models.CharField(max_length=10, choices=NUMBER_FORMAT_CHOICES, default='indian')

    # — Date & Time —
    date_format = models.CharField(max_length=20, choices=DATE_FORMAT_CHOICES, default='j M Y')
    fiscal_year_start = models.PositiveSmallIntegerField(
        default=4, choices=MONTH_CHOICES,
        help_text='Month the financial year begins (1 = Jan, 4 = Apr)'
    )

    # — Business Identity —
    business_name = models.CharField(max_length=200, default='My Business')
    business_tagline = models.CharField(max_length=300, blank=True)
    business_address = models.TextField(blank=True)
    business_phone = models.CharField(max_length=50, blank=True)
    business_email = models.EmailField(blank=True)
    business_website = models.URLField(blank=True)
    tax_number = models.CharField(max_length=100, blank=True,
                                  help_text='GST / VAT / PAN number shown on documents')

    # — Document Defaults —
    invoice_prefix = models.CharField(max_length=20, default='INV')
    quote_prefix = models.CharField(max_length=20, default='Q')
    default_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Default tax % applied on new invoices / quotes'
    )
    default_payment_terms = models.TextField(
        blank=True,
        default='Payment due within 30 days of invoice date.'
    )

    # — Payment Gateway —
    razorpay_key_id = models.CharField(max_length=100, blank=True)
    razorpay_key_secret = models.CharField(max_length=100, blank=True)
    razorpay_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        # Bust in-process filter cache so changes take effect immediately
        try:
            from dashboard.templatetags import clrt_filters
            clrt_filters._settings_cache.clear()
        except Exception:
            pass


class Tag(models.Model):
    COLOR_CHOICES = [
        ('#6366f1', 'Indigo'),
        ('#3b82f6', 'Blue'),
        ('#10b981', 'Green'),
        ('#f59e0b', 'Amber'),
        ('#ef4444', 'Red'),
        ('#8b5cf6', 'Purple'),
        ('#06b6d4', 'Cyan'),
        ('#f97316', 'Orange'),
        ('#64748b', 'Slate'),
        ('#ec4899', 'Pink'),
    ]
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#6366f1')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Notification(models.Model):
    TYPE_CHOICES = [
        ('lead', 'Lead'),
        ('followup', 'Follow-up'),
        ('invoice', 'Invoice'),
        ('contract', 'Contract'),
        ('system', 'System'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=400, blank=True)
    link = models.CharField(max_length=300, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @classmethod
    def push(cls, user, title, body='', link='', type='system'):
        """Create a notification; silently skips if user is None."""
        if user is None:
            return
        cls.objects.create(user=user, title=title, body=body, link=link, type=type)


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('status_changed', 'Status Changed'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} #{self.object_id}"
