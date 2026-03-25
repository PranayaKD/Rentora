from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    try:
        denom = float(arg)
        if denom == 0:
            return 0
        return float(value) / denom
    except (ValueError, TypeError):
        return 0
