"""
Thin helper for logging ActivityEvent records.
Call log_event() from any view after a meaningful action.
"""
from django.contrib.contenttypes.models import ContentType


def log_event(obj, event_type, actor=None, description="", metadata=None):
    from dashboard.models import ActivityEvent
    ActivityEvent.objects.create(
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
        event_type=event_type,
        actor=actor,
        description=description,
        metadata=metadata or {},
    )


def get_events_for(obj, limit=50):
    from dashboard.models import ActivityEvent
    ct = ContentType.objects.get_for_model(obj)
    return ActivityEvent.objects.filter(
        content_type=ct, object_id=obj.pk
    ).select_related("actor")[:limit]
