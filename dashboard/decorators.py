from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def requires_feature(feature):
    """Gate a view behind a plan feature flag.

    Usage:
        @requires_feature('has_reports')
        def my_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            from .models import Subscription
            sub = Subscription.current()
            if sub is None or not getattr(sub.plan, feature, False):
                return render(request, "dashboard/upgrade_required.html", {
                    "feature": feature,
                    "current_sub": sub,
                })
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_limit(model_class, plan_field):
    """Return True if usage is under the plan limit (0 = unlimited)."""
    from .models import Subscription
    sub = Subscription.current()
    if sub is None:
        return False
    limit = getattr(sub.plan, plan_field, 0)
    if limit == 0:
        return True
    return model_class.objects.count() < limit
