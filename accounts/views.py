import io
import base64
import pyotp
import qrcode

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
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
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        if totp.verify(code, valid_window=1):
            user.totp_enabled = True
            user.save(update_fields=["totp_enabled"])
            request.session["2fa_verified"] = True
            messages.success(request, "Two-factor authentication enabled.")
            return redirect("accounts:profile")
        else:
            error = "Invalid code. Try again."

    return render(request, "accounts/two_factor_setup.html", {
        "qr_b64": qr_b64,
        "secret": user.totp_secret,
        "enabled": user.totp_enabled,
        "error": error,
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
        return redirect("/")
    if request.session.get("2fa_verified"):
        return redirect(request.GET.get("next", "/"))

    error = None
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        totp = pyotp.TOTP(request.user.totp_secret)
        if totp.verify(code, valid_window=1):
            request.session["2fa_verified"] = True
            return redirect(request.POST.get("next", "/"))
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
        form.save()
        messages.success(request, "User created successfully.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "Add User"})
