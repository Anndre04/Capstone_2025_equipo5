from django import template

register = template.Library()

@register.filter
def clp(value):
    try:
        value = float(value)
        return "${:,.0f}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return value
    

@register.simple_tag
def get_disponibilidad_dia(disponibilidades, anuncio_id, dia):
    if anuncio_id in disponibilidades:
        for disp in disponibilidades[anuncio_id]:
            if disp.dia == dia:
                return disp
    return None

@register.filter
def get_item(dictionary, key):
    """Permite acceder a un valor de diccionario usando una variable como clave."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}