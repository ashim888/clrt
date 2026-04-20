"""
One-shot project file generator for CLRT Django project.
Run: python setup_project.py
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as f:
        f.write(content)
    print(f"  wrote {path}")

# ─── core/settings.py ────────────────────────────────────────────────────────
write('core/settings.py', '''from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-clrt-dev-secret")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_tailwind",
    "accounts",
    "leads",
    "clients",
    "billing",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "core.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = []
AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"
''')

# ─── core/urls.py ─────────────────────────────────────────────────────────────
write('core/urls.py', '''from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("leads/", include("leads.urls")),
    path("clients/", include("clients.urls")),
    path("billing/", include("billing.urls")),
    path("", include("dashboard.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
''')

# ─── accounts/models.py ───────────────────────────────────────────────────────
write('accounts/models.py', '''from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("sales", "Sales/Marketing"),
        ("accounts", "Accounts"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="sales")

    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def is_sales(self):
        return self.role == "sales"

    def is_accounts(self):
        return self.role == "accounts"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
''')

# ─── accounts/forms.py ────────────────────────────────────────────────────────
write('accounts/forms.py', '''from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username", "class": "input"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password", "class": "input"}))


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "password1", "password2"]
''')

# ─── accounts/views.py ────────────────────────────────────────────────────────
write('accounts/views.py', '''from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, UserCreateForm
from .models import User


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"


class LogoutView(auth_views.LogoutView):
    pass


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"user": request.user})


@login_required
def user_list(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    users = User.objects.all().order_by("username")
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
def user_create(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "User created successfully.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "Add User"})
''')

# ─── accounts/urls.py ─────────────────────────────────────────────────────────
write('accounts/urls.py', '''from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_create, name="user_create"),
]
''')

write('accounts/admin.py', '''from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "is_active"]
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
''')

# ─── leads/models.py ──────────────────────────────────────────────────────────
write('leads/models.py', '''from django.db import models
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
''')

# ─── leads/forms.py ───────────────────────────────────────────────────────────
write('leads/forms.py', '''from django import forms
from .models import Lead, Activity
from accounts.models import User


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["organization_name", "contact_person", "phone", "email", "status", "assigned_to", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True)


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["type", "notes", "next_follow_up_date"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "next_follow_up_date": forms.DateInput(attrs={"type": "date"}),
        }
''')

# ─── leads/views.py ───────────────────────────────────────────────────────────
write('leads/views.py', '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Lead, Activity
from .forms import LeadForm, ActivityForm


def _can_edit_leads(user):
    return user.role in ("admin", "sales") or user.is_superuser


@login_required
def lead_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    leads = Lead.objects.select_related("assigned_to")
    if q:
        leads = leads.filter(
            Q(organization_name__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(phone__icontains=q)
        )
    if status:
        leads = leads.filter(status=status)
    return render(request, "leads/lead_list.html", {
        "leads": leads,
        "q": q,
        "status": status,
        "status_choices": Lead.STATUS_CHOICES,
    })


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    activities = lead.activities.select_related("created_by")
    return render(request, "leads/lead_detail.html", {"lead": lead, "activities": activities})


@login_required
def lead_create(request):
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_list")
    form = LeadForm(request.POST or None)
    if form.is_valid():
        lead = form.save()
        messages.success(request, f"Lead \\"{lead.organization_name}\\" created.")
        return redirect("leads:lead_detail", pk=lead.pk)
    return render(request, "leads/lead_form.html", {"form": form, "title": "Add Lead"})


@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_detail", pk=pk)
    form = LeadForm(request.POST or None, instance=lead)
    if form.is_valid():
        form.save()
        messages.success(request, "Lead updated.")
        return redirect("leads:lead_detail", pk=pk)
    return render(request, "leads/lead_form.html", {"form": form, "title": "Edit Lead", "lead": lead})


@login_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("leads:lead_detail", pk=pk)
    if request.method == "POST":
        lead.delete()
        messages.success(request, "Lead deleted.")
        return redirect("leads:lead_list")
    return render(request, "leads/lead_confirm_delete.html", {"lead": lead})


@login_required
def activity_add(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk)
    form = ActivityForm(request.POST or None)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.lead = lead
        activity.created_by = request.user
        activity.save()
        messages.success(request, "Activity logged.")
        return redirect("leads:lead_detail", pk=lead_pk)
    return render(request, "leads/activity_form.html", {"form": form, "lead": lead})


@login_required
def convert_to_client(request, pk):
    from clients.models import Client
    lead = get_object_or_404(Lead, pk=pk)
    if lead.status != "won":
        messages.error(request, "Only Won leads can be converted to clients.")
        return redirect("leads:lead_detail", pk=pk)
    if hasattr(lead, "client"):
        messages.info(request, "Already converted.")
        return redirect("clients:client_detail", pk=lead.client.pk)
    if request.method == "POST":
        client = Client.objects.create(
            organization_name=lead.organization_name,
            linked_lead=lead,
        )
        messages.success(request, f"Lead converted to client: {client.organization_name}")
        return redirect("clients:client_detail", pk=client.pk)
    return render(request, "leads/convert_confirm.html", {"lead": lead})
''')

# ─── leads/urls.py ────────────────────────────────────────────────────────────
write('leads/urls.py', '''from django.urls import path
from . import views

app_name = "leads"

urlpatterns = [
    path("", views.lead_list, name="lead_list"),
    path("add/", views.lead_create, name="lead_create"),
    path("<int:pk>/", views.lead_detail, name="lead_detail"),
    path("<int:pk>/edit/", views.lead_edit, name="lead_edit"),
    path("<int:pk>/delete/", views.lead_delete, name="lead_delete"),
    path("<int:lead_pk>/activity/add/", views.activity_add, name="activity_add"),
    path("<int:pk>/convert/", views.convert_to_client, name="convert_to_client"),
]
''')

write('leads/admin.py', '''from django.contrib import admin
from .models import Lead, Activity

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["organization_name", "contact_person", "status", "assigned_to", "created_at"]
    list_filter = ["status", "assigned_to"]
    search_fields = ["organization_name", "contact_person", "phone"]

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["lead", "type", "next_follow_up_date", "created_by", "created_at"]
    list_filter = ["type"]
''')

# ─── clients/models.py ────────────────────────────────────────────────────────
write('clients/models.py', '''from django.db import models
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
''')

# ─── clients/forms.py ─────────────────────────────────────────────────────────
write('clients/forms.py', '''from django import forms
from .models import Client, Contract


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["organization_name", "phone", "email", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["contract_title", "start_date", "end_date", "billing_cycle",
                  "contract_value", "document", "status", "notes"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
''')

# ─── clients/views.py ─────────────────────────────────────────────────────────
write('clients/views.py', '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Client, Contract
from .forms import ClientForm, ContractForm


@login_required
def client_list(request):
    q = request.GET.get("q", "")
    clients = Client.objects.all()
    if q:
        clients = clients.filter(
            Q(organization_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
        )
    return render(request, "clients/client_list.html", {"clients": clients, "q": q})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    contracts = client.contracts.all()
    return render(request, "clients/client_detail.html", {"client": client, "contracts": contracts})


@login_required
def client_create(request):
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("clients:client_list")
    form = ClientForm(request.POST or None)
    if form.is_valid():
        client = form.save()
        messages.success(request, f"Client \\"{client.organization_name}\\" created.")
        return redirect("clients:client_detail", pk=client.pk)
    return render(request, "clients/client_form.html", {"form": form, "title": "Add Client"})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("clients:client_detail", pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        messages.success(request, "Client updated.")
        return redirect("clients:client_detail", pk=pk)
    return render(request, "clients/client_form.html", {"form": form, "title": "Edit Client", "client": client})


@login_required
def contract_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("clients:client_detail", pk=client_pk)
    form = ContractForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        contract = form.save(commit=False)
        contract.client = client
        contract.save()
        messages.success(request, "Contract created.")
        return redirect("clients:contract_detail", pk=contract.pk)
    return render(request, "clients/contract_form.html", {"form": form, "client": client, "title": "Add Contract"})


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, "clients/contract_detail.html", {"contract": contract})


@login_required
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_detail", pk=pk)
    form = ContractForm(request.POST or None, request.FILES or None, instance=contract)
    if form.is_valid():
        form.save()
        messages.success(request, "Contract updated.")
        return redirect("clients:contract_detail", pk=pk)
    return render(request, "clients/contract_form.html", {"form": form, "title": "Edit Contract", "contract": contract})
''')

# ─── clients/urls.py ──────────────────────────────────────────────────────────
write('clients/urls.py', '''from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="client_list"),
    path("add/", views.client_create, name="client_create"),
    path("<int:pk>/", views.client_detail, name="client_detail"),
    path("<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("<int:client_pk>/contracts/add/", views.contract_create, name="contract_create"),
    path("contracts/<int:pk>/", views.contract_detail, name="contract_detail"),
    path("contracts/<int:pk>/edit/", views.contract_edit, name="contract_edit"),
]
''')

write('clients/admin.py', '''from django.contrib import admin
from .models import Client, Contract

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["organization_name", "email", "phone", "created_at"]
    search_fields = ["organization_name", "email"]

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["contract_title", "client", "start_date", "end_date", "status", "billing_cycle"]
    list_filter = ["status", "billing_cycle"]
''')

# ─── billing/models.py ────────────────────────────────────────────────────────
write('billing/models.py', '''from django.db import models
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
''')

# ─── billing/forms.py ─────────────────────────────────────────────────────────
write('billing/forms.py', '''from django import forms
from .models import Invoice, Payment
from clients.models import Client, Contract
import uuid


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["client", "contract", "invoice_number", "amount", "due_date", "description"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        client_pk = kwargs.pop("client_pk", None)
        super().__init__(*args, **kwargs)
        if client_pk:
            self.fields["contract"].queryset = Contract.objects.filter(client_id=client_pk)
        if not self.instance.pk:
            self.fields["invoice_number"].initial = f"INV-{uuid.uuid4().hex[:8].upper()}"


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount_paid", "payment_date", "payment_mode", "reference", "notes"]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
''')

# ─── billing/views.py ─────────────────────────────────────────────────────────
write('billing/views.py', '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import Invoice, Payment
from .forms import InvoiceForm, PaymentForm
from clients.models import Client


@login_required
def invoice_list(request):
    status = request.GET.get("status", "")
    q = request.GET.get("q", "")
    invoices = Invoice.objects.select_related("client", "contract")
    if status:
        invoices = invoices.filter(status=status)
    if q:
        invoices = invoices.filter(
            Q(client__organization_name__icontains=q) | Q(invoice_number__icontains=q)
        )
    return render(request, "billing/invoice_list.html", {
        "invoices": invoices,
        "status": status,
        "q": q,
        "status_choices": Invoice.STATUS_CHOICES,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = invoice.payments.all()
    paid_total = payments.aggregate(t=Sum("amount_paid"))["t"] or 0
    return render(request, "billing/invoice_detail.html", {
        "invoice": invoice,
        "payments": payments,
        "paid_total": paid_total,
        "balance": invoice.amount - paid_total,
    })


@login_required
def invoice_create(request):
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:invoice_list")
    form = InvoiceForm(request.POST or None)
    if form.is_valid():
        invoice = form.save()
        messages.success(request, f"Invoice {invoice.invoice_number} created.")
        return redirect("billing:invoice_detail", pk=invoice.pk)
    return render(request, "billing/invoice_form.html", {"form": form, "title": "Create Invoice"})


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:invoice_detail", pk=pk)
    form = InvoiceForm(request.POST or None, instance=invoice)
    if form.is_valid():
        form.save()
        messages.success(request, "Invoice updated.")
        return redirect("billing:invoice_detail", pk=pk)
    return render(request, "billing/invoice_form.html", {"form": form, "title": "Edit Invoice", "invoice": invoice})


@login_required
def mark_overdue(request):
    from django.utils import timezone
    updated = Invoice.objects.filter(
        status="pending", due_date__lt=timezone.now().date()
    ).update(status="overdue")
    messages.success(request, f"{updated} invoice(s) marked as overdue.")
    return redirect("billing:invoice_list")


@login_required
def payment_add(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:invoice_detail", pk=invoice_pk)
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.invoice = invoice
        payment.save()
        # Check if invoice is fully paid
        paid_total = invoice.payments.aggregate(t=__import__("django.db.models", fromlist=["Sum"]).Sum("amount_paid"))["t"] or 0
        if paid_total >= invoice.amount:
            invoice.status = "paid"
            invoice.save()
        messages.success(request, "Payment recorded.")
        return redirect("billing:invoice_detail", pk=invoice_pk)
    return render(request, "billing/payment_form.html", {"form": form, "invoice": invoice})
''')

# ─── billing/urls.py ──────────────────────────────────────────────────────────
write('billing/urls.py', '''from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("add/", views.invoice_create, name="invoice_create"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
    path("mark-overdue/", views.mark_overdue, name="mark_overdue"),
    path("<int:invoice_pk>/payment/add/", views.payment_add, name="payment_add"),
]
''')

write('billing/admin.py', '''from django.contrib import admin
from .models import Invoice, Payment

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "client", "amount", "due_date", "status"]
    list_filter = ["status"]
    search_fields = ["invoice_number", "client__organization_name"]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice", "amount_paid", "payment_date", "payment_mode"]
''')

# ─── dashboard/views.py ───────────────────────────────────────────────────────
write('dashboard/views.py', '''from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from leads.models import Lead, Activity
from clients.models import Contract
from billing.models import Invoice


@login_required
def dashboard(request):
    today = timezone.now().date()
    in_30_days = today + timezone.timedelta(days=30)

    # Today\'s and overdue follow-ups
    todays_followups = Activity.objects.filter(
        next_follow_up_date=today
    ).select_related("lead", "created_by")

    overdue_followups = Activity.objects.filter(
        next_follow_up_date__lt=today,
        lead__status__in=["new", "contacted", "demo", "negotiation"]
    ).select_related("lead").order_by("next_follow_up_date")

    # Contracts expiring in 30 days
    expiring_contracts = Contract.objects.filter(
        status="active",
        end_date__gte=today,
        end_date__lte=in_30_days
    ).select_related("client").order_by("end_date")

    # Pending/overdue invoices
    pending_invoices = Invoice.objects.filter(
        status__in=["pending", "overdue"]
    ).select_related("client").order_by("due_date")

    # Revenue summary
    paid_this_month = Invoice.objects.filter(
        status="paid",
        generated_date__year=today.year,
        generated_date__month=today.month,
    )
    from django.db.models import Sum
    revenue_month = paid_this_month.aggregate(t=Sum("amount"))["t"] or 0

    lead_stats = {
        "total": Lead.objects.count(),
        "new": Lead.objects.filter(status="new").count(),
        "won": Lead.objects.filter(status="won").count(),
        "lost": Lead.objects.filter(status="lost").count(),
    }

    return render(request, "dashboard/dashboard.html", {
        "today": today,
        "todays_followups": todays_followups,
        "overdue_followups": overdue_followups,
        "expiring_contracts": expiring_contracts,
        "pending_invoices": pending_invoices,
        "revenue_month": revenue_month,
        "lead_stats": lead_stats,
    })
''')

# ─── dashboard/urls.py ────────────────────────────────────────────────────────
write('dashboard/urls.py', '''from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
''')

write('dashboard/admin.py', 'from django.contrib import admin\n')

# ─── management command: check_alerts ─────────────────────────────────────────
write('dashboard/management/__init__.py', '')
write('dashboard/management/commands/__init__.py', '')
write('dashboard/management/commands/check_alerts.py', '''"""
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
''')

print("\\n[OK] All Python files written.")
