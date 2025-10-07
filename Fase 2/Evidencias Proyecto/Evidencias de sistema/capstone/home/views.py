from django.shortcuts import render
from tutoria.models import Anuncio
from autenticacion.models import AreaInteres

# Create your views here.

def home(request):

    anuncios = Anuncio.objects.filter(activo=True)

    areainteres = AreaInteres.objects.all()

    contexto = {
        "anuncios": anuncios,
        "areas" : areainteres
    }

    return render(request, 'home/home.html', contexto)

