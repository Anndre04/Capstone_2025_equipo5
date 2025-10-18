from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from tutoria.models import Tutoria

@login_required
def index(request, tutoria_id):
    tutoria = get_object_or_404(Tutoria, id=tutoria_id)

    # Validación: solo el tutor o estudiante puede acceder
    if request.user != tutoria.tutor.usuario and request.user != tutoria.estudiante:
        return render(request, "acceso_denegado.html", {
            "mensaje": "No tienes permiso para acceder a esta videollamada."
        })

    return render(request, "index.html", {"tutoria": tutoria})
