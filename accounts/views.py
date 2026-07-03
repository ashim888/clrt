import io
import base64
import pyotp
import qrcode

from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetView as _PasswordResetView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .forms import LoginForm, UserCreateForm, UserEditForm, AdminSetPasswordForm, SelfPasswordChangeForm


class PasswordResetView(_PasswordResetView):
    """Wraps Django's built-in view to catch SMTP errors gracefully."""
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = "/accounts/forgot-password/sent/"

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            messages.error(
                self.request,
                f"Could not send reset email: {e}. Check your email settings.",
            )
            return self.render_to_response(self.get_context_data(form=form))


def _send_invite_email(request, user):
    from dashboard.models import SiteSettings
    cfg = SiteSettings.load()
    site_url = getattr(__import__("django.conf", fromlist=["settings"]).settings, "SITE_URL", request.build_absolute_uri("/").rstrip("/"))
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{site_url}/accounts/reset/{uid}/{token}/"
    body = (
        f"Hi {user.get_full_name() or user.username},\n\n"
        f"An account has been created for you on {cfg.business_name}.\n\n"
        f"Username: {user.username}\n\n"
        f"Set your password here:\n{reset_url}\n\n"
        f"This link expires in 3 days.\n\n"
        f"— {cfg.business_name} Team"
    )
    try:
        send_mail(
            subject=f"You're invited to {cfg.business_name}",
            message=body,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass
from .models import User


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def get_success_url(self):
        from dashboard.models import SiteSettings
        cfg = SiteSettings.load()
        if cfg.require_2fa and getattr(self.request.user, "totp_enabled", False):
            next_url = self.request.POST.get(
                "next", self.request.GET.get("next", "/dashboard/")
            )
            return f"/accounts/2fa/verify/?next={next_url}"
        return super().get_success_url()


class LogoutView(auth_views.LogoutView):
    pass


@login_required
def profile(request):
    user = request.user
    # Always generate QR so it's ready to show inline on the profile page
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save(update_fields=["totp_secret"])
    totp = pyotp.TOTP(user.totp_secret)
    uri = totp.provisioning_uri(name=user.email or user.username, issuer_name="CLRT")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return render(request, "accounts/profile.html", {
        "user": user,
        "qr_b64": qr_b64,
        "totp_secret": user.totp_secret,
    })


@login_required
def user_list(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    qs = User.objects.all()
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")
    q = request.GET.get("q", "")
    if role:
        qs = qs.filter(role=role)
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "inactive":
        qs = qs.filter(is_active=False)
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    qs = qs.order_by("is_active", "first_name", "username")
    return render(request, "accounts/user_list.html", {
        "users": qs,
        "role_choices": User.ROLE_CHOICES,
        "role": role,
        "status": status,
        "q": q,
    })


@login_required
def two_factor_setup(request):
    """Show QR code and let user enable TOTP."""
    user = request.user

    # Generate a new secret if user doesn't have one yet
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save(update_fields=["totp_secret"])

    totp = pyotp.TOTP(user.totp_secret)
    uri = totp.provisioning_uri(
        name=user.email or user.username,
        issuer_name="CLRT",
    )

    # Generate QR code as base64 PNG
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    error = None
    from dashboard.models import SiteSettings
    forced = SiteSettings.load().require_2fa and not user.totp_enabled

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        if totp.verify(code, valid_window=1):
            user.totp_enabled = True
            user.save(update_fields=["totp_enabled"])
            request.session["2fa_verified"] = True
            messages.success(request, "Two-factor authentication enabled.")
            return redirect(request.POST.get("next", "/dashboard/"))
        else:
            messages.error(request, "Invalid code — please try again.")

    # GET: render standalone setup page
    return render(request, "accounts/two_factor_setup.html", {
        "qr_b64": qr_b64,
        "secret": user.totp_secret,
        "enabled": user.totp_enabled,
        "forced": forced,
        "next": request.GET.get("next", "/dashboard/"),
        "error": None,
    })


@login_required
@require_POST
def two_factor_disable(request):
    """Disable 2FA after verifying current TOTP code."""
    user = request.user
    code = request.POST.get("code", "").strip()
    totp = pyotp.TOTP(user.totp_secret)
    if totp.verify(code, valid_window=1):
        user.totp_enabled = False
        user.totp_secret = ""
        user.save(update_fields=["totp_enabled", "totp_secret"])
        request.session.pop("2fa_verified", None)
        messages.success(request, "Two-factor authentication disabled.")
    else:
        messages.error(request, "Invalid code — 2FA not disabled.")
    return redirect("accounts:two_factor_setup")


def two_factor_verify(request):
    """Post-login step: verify TOTP before granting full session access."""
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if not getattr(request.user, "totp_enabled", False):
        return redirect("/dashboard/")
    if request.session.get("2fa_verified"):
        return redirect(request.GET.get("next", "/dashboard/"))

    error = None
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        totp = pyotp.TOTP(request.user.totp_secret)
        if totp.verify(code, valid_window=1):
            request.session["2fa_verified"] = True
            return redirect(request.POST.get("next", "/dashboard/"))
        else:
            error = "Invalid code. Check your authenticator app and try again."

    return render(request, "accounts/two_factor_verify.html", {
        "next": request.GET.get("next", "/"),
        "error": error,
    })


@login_required
def user_create(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        send_invite = request.POST.get("send_invite") == "1"
        if send_invite and user.email:
            _send_invite_email(request, user)
        messages.success(request, f"User '{user.username}' created." + (" Invite email sent." if send_invite and user.email else ""))
        return redirect("accounts:user_detail", pk=user.pk)
    return render(request, "accounts/user_form.html", {"form": form, "title": "Add User"})


@login_required
def user_detail(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    u = get_object_or_404(User, pk=pk)
    from leads.models import Activity, Lead
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    import json

    activities = Activity.objects.filter(created_by=u).select_related("lead").order_by("-created_at")[:20]
    lead_stats = Lead.objects.filter(assigned_to=u).aggregate(
        total=Count("pk"),
        won=Count("pk", filter=Q(status="won")),
        active=Count("pk", filter=Q(status__in=["new", "contacted", "demo", "negotiation"])),
    )

    # 6-month performance chart data
    today = timezone.localdate()
    chart_labels = []
    chart_activities = []
    chart_won = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        chart_labels.append(month_start.strftime("%b %Y"))
        chart_activities.append(
            Activity.objects.filter(created_by=u, created_at__date__gte=month_start, created_at__date__lt=month_end).count()
        )
        chart_won.append(
            Lead.objects.filter(assigned_to=u, status="won", updated_at__date__gte=month_start, updated_at__date__lt=month_end).count()
        )

    active_users = User.objects.filter(is_active=True).exclude(pk=u.pk).order_by("first_name", "username")

    return render(request, "accounts/user_detail.html", {
        "u": u,
        "activities": activities,
        "lead_stats": lead_stats,
        "chart_labels": json.dumps(chart_labels),
        "chart_activities": json.dumps(chart_activities),
        "chart_won": json.dumps(chart_won),
        "active_users": active_users,
    })


@login_required
def user_edit(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    u = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=u)
    if form.is_valid():
        form.save()
        messages.success(request, f"User '{u.username}' updated.")
        return redirect("accounts:user_detail", pk=pk)
    return render(request, "accounts/user_form.html", {"form": form, "title": f"Edit {u.get_full_name() or u.username}", "editing": True, "u": u})


@login_required
@require_POST
def user_set_password(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    u = get_object_or_404(User, pk=pk)
    form = AdminSetPasswordForm(request.POST)
    if form.is_valid():
        u.set_password(form.cleaned_data["new_password1"])
        u.save(update_fields=["password"])
        messages.success(request, f"Password for '{u.username}' updated.")
    else:
        for err in form.errors.values():
            messages.error(request, err.as_text())
    return redirect("accounts:user_detail", pk=pk)


@login_required
@require_POST
def user_toggle_active(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    u = get_object_or_404(User, pk=pk)
    if u == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("accounts:user_detail", pk=pk)
    deactivating = u.is_active
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    if deactivating:
        # Reassign open leads if requested
        reassign_to_id = request.POST.get("reassign_to", "").strip()
        if reassign_to_id:
            new_owner = User.objects.filter(pk=reassign_to_id, is_active=True).first()
            if new_owner:
                from leads.models import Lead
                count = Lead.objects.filter(
                    assigned_to=u,
                    status__in=["new", "contacted", "demo", "negotiation"]
                ).update(assigned_to=new_owner)
                messages.info(request, f"{count} active lead(s) reassigned to {new_owner.get_full_name() or new_owner.username}.")
        # Force all sessions out
        u.session_version = (u.session_version or 0) + 1
        u.save(update_fields=["session_version"])
    messages.success(request, f"User '{u.username}' {'deactivated' if deactivating else 'reactivated'}.")
    return redirect("accounts:user_detail", pk=pk)


@login_required
@require_POST
def user_force_logout(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    u = get_object_or_404(User, pk=pk)
    if u == request.user:
        messages.error(request, "You cannot force-logout your own account.")
        return redirect("accounts:user_detail", pk=pk)
    u.session_version = (u.session_version or 0) + 1
    u.save(update_fields=["session_version"])
    messages.success(request, f"All sessions for '{u.username}' have been terminated.")
    return redirect("accounts:user_detail", pk=pk)


@login_required
@require_POST
def user_reset_2fa(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    u = get_object_or_404(User, pk=pk)
    u.totp_enabled = False
    u.totp_secret = ""
    u.session_version = (u.session_version or 0) + 1  # invalidate sessions
    u.save(update_fields=["totp_enabled", "totp_secret", "session_version"])
    messages.success(request, f"2FA reset for '{u.username}'. They will be prompted to re-enroll on next login.")
    return redirect("accounts:user_detail", pk=pk)


@login_required
@require_POST
def user_change_own_password(request):
    form = SelfPasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        request.user.set_password(form.cleaned_data["new_password1"])
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        messages.success(request, "Password changed successfully.")
    else:
        for err in form.errors.values():
            messages.error(request, err.as_text())
    return redirect("accounts:profile")
