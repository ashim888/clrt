from django.shortcuts import redirect

# Paths that are always accessible regardless of 2FA state
_EXEMPT = {
    "/accounts/login/",
    "/accounts/logout/",
    "/accounts/2fa/verify/",
    "/accounts/2fa/setup/",
    "/accounts/2fa/disable/",
    "/accounts/forgot-password/",
    "/accounts/forgot-password/sent/",
}

# Prefix-exempt: any path starting with these is exempt
_EXEMPT_PREFIXES = (
    "/accounts/reset/",
)


def _2fa_required():
    try:
        from dashboard.models import SiteSettings
        return SiteSettings.load().require_2fa
    except Exception:
        return False


class TwoFactorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # ── Force-logout: session version check ──────────────────
            stored_ver = request.session.get("session_version")
            current_ver = getattr(request.user, "session_version", 0)
            if stored_ver is None:
                request.session["session_version"] = current_ver
            elif stored_ver != current_ver:
                request.session.flush()
                return redirect("/accounts/login/?next=" + request.path)

            # ── 2FA gate ──────────────────────────────────────────────
            path = request.path
            is_exempt = path in _EXEMPT or any(path.startswith(p) for p in _EXEMPT_PREFIXES)

            if _2fa_required() and not is_exempt:
                if not getattr(request.user, "totp_enabled", False):
                    # Not set up yet — send to setup page
                    return redirect("/accounts/2fa/setup/")
                elif not request.session.get("2fa_verified"):
                    # Set up but not verified this session — send to verify
                    return redirect(f"/accounts/2fa/verify/?next={path}")

        return self.get_response(request)
