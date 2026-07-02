def log_audit(user, action, obj, changes=None):
    from .models import AuditLog
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=type(obj).__name__,
        object_id=obj.pk,
        object_repr=str(obj)[:200],
        changes=changes or {},
    )


def model_changes(old_obj, new_obj, fields):
    """Return dict of {field: [old_str, new_str]} for fields that changed."""
    out = {}
    for f in fields:
        old = getattr(old_obj, f, None)
        new = getattr(new_obj, f, None)
        if str(old) != str(new):
            out[f] = [str(old) if old is not None else '', str(new) if new is not None else '']
    return out
