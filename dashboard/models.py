from django.conf import settings
from django.db import models
from dashboard.fields import EncryptedCharField


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
    business_logo = models.ImageField(upload_to='business/', blank=True)
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
        help_text='VAT/tax % automatically pre-filled on new quotations and invoices'
    )
    max_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Maximum discount % allowed on any quotation or invoice (0 = no limit)'
    )
    default_payment_terms = models.TextField(
        blank=True,
        default='Payment due within 30 days of invoice date.'
    )
    default_quote_terms = models.TextField(
        blank=True,
        help_text='Pre-filled on every new quotation; supports "Label: text" format for bold labels on print'
    )

    # — Payment Gateway —
    razorpay_key_id = EncryptedCharField(max_length=500, blank=True)
    razorpay_key_secret = EncryptedCharField(max_length=500, blank=True)
    razorpay_enabled = models.BooleanField(default=False)

    # — Security —
    require_2fa = models.BooleanField(
        default=False,
        help_text='Require all users to verify via Google Authenticator after login',
    )

    # — Analytics —
    ga_measurement_id = models.CharField(
        max_length=30, blank=True,
        help_text='Google Analytics 4 Measurement ID (e.g. G-XXXXXXXXXX)',
    )

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


class CalendarEvent(models.Model):
    COLOR_CHOICES = [
        ('#6366f1', 'Indigo'), ('#3b82f6', 'Blue'), ('#10b981', 'Green'),
        ('#f59e0b', 'Amber'), ('#ef4444', 'Red'), ('#8b5cf6', 'Purple'),
        ('#06b6d4', 'Cyan'), ('#f97316', 'Orange'), ('#ec4899', 'Pink'),
    ]
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6366f1')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='calendar_events',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start']

    def __str__(self):
        return self.title


class UserGoal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals'
    )
    month = models.DateField(help_text='Always the 1st of the target month')
    target = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = [('user', 'month')]
        ordering = ['-month']

    def __str__(self):
        return f"{self.user} — {self.month.strftime('%b %Y')} target"


class QuickNote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='quick_notes',
    )
    lead = models.ForeignKey(
        'leads.Lead', on_delete=models.CASCADE,
        null=True, blank=True, related_name='quick_notes',
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE,
        null=True, blank=True, related_name='quick_notes',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.body[:50]}"


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


# ── Analytics ────────────────────────────────────────────────────

class PageEvent(models.Model):
    session_id = models.CharField(max_length=100, db_index=True)
    event = models.CharField(max_length=60, db_index=True)
    page = models.CharField(max_length=200)
    referrer = models.CharField(max_length=500, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event} @ {self.page} [{self.timestamp:%Y-%m-%d %H:%M}]"


# ── Plans & Subscriptions ────────────────────────────────────────

class Plan(models.Model):
    SLUG_CHOICES = [
        ('starter', 'Starter'),
        ('growth', 'Growth'),
        ('enterprise', 'Enterprise'),
    ]
    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=20, unique=True, choices=SLUG_CHOICES)
    tagline = models.CharField(max_length=120, blank=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    # Hard limits (0 = unlimited)
    max_leads = models.PositiveIntegerField(default=100)
    max_clients = models.PositiveIntegerField(default=20)
    max_users = models.PositiveIntegerField(default=2)
    max_invoices = models.PositiveIntegerField(default=50)

    # Feature flags
    has_reports = models.BooleanField(default=False)
    has_proposals = models.BooleanField(default=False)
    has_razorpay = models.BooleanField(default=False)
    has_client_portal = models.BooleanField(default=False)
    has_web_capture = models.BooleanField(default=False)
    has_quota_tracking = models.BooleanField(default=False)
    has_audit_log = models.BooleanField(default=False)
    has_calendar = models.BooleanField(default=True)
    has_catalog = models.BooleanField(default=False)
    has_custom_branding = models.BooleanField(default=False)

    custom_features = models.JSONField(
        default=list, blank=True,
        help_text='List of feature strings shown on pricing page. Overrides auto-generated list when non-empty.',
    )

    class Meta:
        ordering = ['price_monthly']

    def __str__(self):
        return self.name

    def limit_label(self, field):
        val = getattr(self, field, 0)
        return 'Unlimited' if val == 0 else str(val)


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('trialing', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    trial_ends = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plan.name} ({self.get_status_display()})"

    @classmethod
    def current(cls):
        from django.utils import timezone
        today = timezone.now().date()
        sub = cls.objects.filter(
            status__in=['active', 'trialing']
        ).select_related('plan').first()
        if sub and sub.status == 'trialing' and sub.trial_ends and sub.trial_ends < today:
            sub.status = 'expired'
            sub.save(update_fields=['status'])
            return None
        return sub

    def is_live(self):
        from django.utils import timezone
        if self.status == 'active':
            return True
        if self.status == 'trialing' and self.trial_ends:
            return self.trial_ends >= timezone.now().date()
        return False
