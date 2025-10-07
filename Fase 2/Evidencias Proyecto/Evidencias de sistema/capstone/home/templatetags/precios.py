from django import template

register = template.Library()

@register.filter
def clp(value):
    try:
        value = float(value)
        return "${:,.0f}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return value