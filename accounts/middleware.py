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
        if (
            request.user.is_authenticated
            and getattr(request.user, "totp_enabled", False)
            and not request.session.get("2fa_verified")
            and request.path not in _EXEMPT
        ):
            return redirect("/accounts/2fa/verify/")
        return self.get_response(request)
