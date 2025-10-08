from django import template

register = template.Library()

@register.filter
def clp(value):
    try:
        value = float(value)
        return "${:,.0f}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return value
    
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])

@register.simple_tag
def get_disponibilidad_dia(disponibilidades, anuncio_id, dia):
    if anuncio_id in disponibilidades:
        for disp in disponibilidades[anuncio_id]:
            if disp.dia == dia:
                return disp
    return None