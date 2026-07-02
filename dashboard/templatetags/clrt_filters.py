import time
from django import template
from django.utils.dateformat import format as _date_fmt

register = template.Library()

# Module-level cache; cleared by SiteSettings.save()
_settings_cache = {}


def _get_settings():
    now = time.monotonic()
    if 'obj' not in _settings_cache or now - _settings_cache.get('ts', 0) > 30:
        try:
            from dashboard.models import SiteSettings
            _settings_cache['obj'] = SiteSettings.load()
            _settings_cache['ts'] = now
        except Exception:
            _settings_cache['obj'] = None
            _settings_cache['ts'] = now
    return _settings_cache.get('obj')


def _indian_commas(val):
    val = round(float(val))
    negative = val < 0
    s = str(abs(val))
    if len(s) <= 3:
        result = s
    else:
        result = s[-3:]
        s = s[:-3]
        while s:
            chunk = s[-2:]
            result = chunk + ',' + result
            s = s[:-2]
    return ('-' if negative else '') + result


def _western_commas(val):
    return f'{round(float(val)):,}'


def _format_number(value, settings):
    fmt = settings.number_format if settings else 'indian'
    return _indian_commas(value) if fmt == 'indian' else _western_commas(value)


@register.filter
def inr(value):
    """Format a monetary value with the configured currency symbol and number format."""
    s = _get_settings()
    symbol = s.currency_symbol if s else 'Rs.'
    if value is None:
        return f'{symbol} 0'
    try:
        fval = float(value)
        if fval == 0:
            return f'{symbol} 0'
        return f'{symbol} {_format_number(value, s)}'
    except (ValueError, TypeError):
        return f'{symbol} 0'


@register.filter
def inr_num(value):
    """Indian/Western formatted number without currency symbol."""
    s = _get_settings()
    if value is None:
        return '0'
    try:
        return _format_number(value, s)
    except (ValueError, TypeError):
        return '0'


@register.filter
def site_date(value):
    """Format a date using the system-configured date format."""
    if not value:
        return ''
    s = _get_settings()
    fmt = s.date_format if s else 'j M Y'
    try:
        return _date_fmt(value, fmt)
    except Exception:
        return str(value)
