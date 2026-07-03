from django.shortcuts import redirect

_EXEMPT = {
    "/accounts/login/",
    "/accounts/logout/",
    "/accounts/2fa/verify/",
    "/accounts/2fa/setup/",
}


class TwoFactorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Force-logout: session version mismatch means admin revoked all sessions
            stored_ver = request.session.get("session_version")
            current_ver = getattr(request.user, "session_version", 0)
            if stored_ver is None:
                # Stamp version on new/existing sessions
                request.session["session_version"] = current_ver
            elif stored_ver != current_ver:
                request.session.flush()
                return redirect("/accounts/login/?next=" + request.path)

            # 2FA gate
            if (
                getattr(request.user, "totp_enabled", False)
                and not request.session.get("2fa_verified")
                and request.path not in _EXEMPT
            ):
                return redirect("/accounts/2fa/verify/")

        return self.get_response(request)
