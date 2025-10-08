from django.shortcuts import render
from tutoria.models import Anuncio, Tutor
from autenticacion.models import AreaInteres

# Create your views here.

def home(request):
    anuncios = Anuncio.objects.filter(activo=True)
    areainteres = AreaInteres.objects.all()

    # Obtener filtros del GET
    nombre = request.GET.get('nombre', '')
    precio_max = request.GET.get('precio_max', '')
    asignatura_id = request.GET.get('asignatura', '')

    print(nombre)
    print(precio_max)
    print(asignatura_id)

    # Filtrar por nombre del tutor
    if nombre:
        anuncios = anuncios.filter(tutor__usuario__nombre__icontains=nombre)

    # Filtrar por precio máximo
    if precio_max:
        anuncios = anuncios.filter(precio__lte=precio_max)

    # Filtrar por asignatura / área de interés
    if asignatura_id:
        anuncios = anuncios.filter(area__id=asignatura_id)

    contexto = {
        "anuncios": anuncios,
        "areas": areainteres,
        "filtros": {
            "nombre": nombre,
            "precio_max": precio_max,
            "asignatura": asignatura_id,
        }
    }

    return render(request, 'home/home.html', contexto)

