from django import template

register = template.Library()


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


@register.filter
def inr(value):
    if value is None:
        return 'Rs. 0'
    try:
        if float(value) == 0:
            return 'Rs. 0'
        return 'Rs. ' + _indian_commas(value)
    except (ValueError, TypeError):
        return 'Rs. 0'


@register.filter
def inr_num(value):
    """Indian-format number without Rs. prefix (for raw amounts)."""
    if value is None:
        return '0'
    try:
        return _indian_commas(value)
    except (ValueError, TypeError):
        return '0'
