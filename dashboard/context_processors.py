def site_settings(request):
    try:
        from dashboard.models import SiteSettings
        return {'site_settings': SiteSettings.load()}
    except Exception:
        return {'site_settings': None}


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    try:
        from dashboard.models import Notification
        qs = Notification.objects.filter(user=request.user)
        return {
            'unread_notification_count': qs.filter(is_read=False).count(),
            'recent_notifications': qs[:8],
        }
    except Exception:
        return {'unread_notification_count': 0, 'recent_notifications': []}


def subscription(request):
    try:
        from dashboard.models import Subscription
        sub = Subscription.current()
        return {
            'current_sub': sub,
            'current_plan': sub.plan if sub else None,
        }
    except Exception:
        return {'current_sub': None, 'current_plan': None}
