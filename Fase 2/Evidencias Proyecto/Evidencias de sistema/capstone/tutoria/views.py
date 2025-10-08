from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Anuncio, TipoSolicitud, Solicitud, Tutor

@login_required
def mistutoriasprof(request, user_id):

    # Obtener el tutor
    tutor = get_object_or_404(Tutor, usuario__id=user_id)
    
    anuncios = Anuncio.objects.filter(tutor=tutor)

    print(anuncios)
    
    contexto = {
        'anuncios': anuncios,
    }

    return render(request, 'tutoria/mistutoriasprof.html', contexto)

@login_required
def anunciotutor(request, anuncio_id):

    anuncio = get_object_or_404(Anuncio, id=anuncio_id)

    contexto = {
        'anuncio' : anuncio
    }
    return render(request, 'tutoria/anunciotutor.html', contexto)

@login_required
def enviar_solicitud(request, anuncio_id):

    # Traemos el anuncio
    anuncio = get_object_or_404(Anuncio, id=anuncio_id)

    # Traemos o creamos el tipo de solicitud "Tutoria"
    tipo = TipoSolicitud.objects.get_or_create(nombre="Alumno")

    # Solo POST para crear solicitud
    if request.method == "POST":
        mensaje = request.POST.get("mensaje", "").strip()
        
        # Verificar que no exista solicitud previa
        if Solicitud.objects.filter(estudiante=request.user, anuncio=anuncio).exists():
            messages.error(request, "Ya enviaste una solicitud a este tutor.")
            return redirect("tutoria:anunciotutor", anuncio_id=anuncio.id)
        
        # Crear la solicitud
        Solicitud.objects.create(
            estudiante=request.user,
            tutor=anuncio.tutor,
            tipo=tipo,
            mensaje=mensaje,
            anuncio=anuncio
        )
        messages.success(request, "Solicitud enviada correctamente.")
        return redirect("tutoria:mis_solicitudes")  # página donde el alumno ve sus solicitudes

    # GET → mostrar formulario
    return render(request, "tutoria/enviar_solicitud.html", {"anuncio": anuncio})

@login_required
def solicitudesprof(request, user_id):

    # Obtener el tutor
    tutor = get_object_or_404(Tutor, usuario__id=user_id)
    
    solicitudes = Solicitud.objects.filter(tutor=tutor, estado='Pendiente')
    
    contexto = {
        'solicitudes': solicitudes,
    }
    
    return render(request, 'tutoria/solicitudesprof.html', contexto)

@login_required
def aceptar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    # Solo el tutor correspondiente puede aceptar
    if solicitud.tutor.usuario != request.user:
        messages.error(request, "No tienes permisos para aceptar esta solicitud.")
        return redirect('tutoria:solicitudesprof', user_id=request.user.id)

    solicitud.estado = "Aceptada"
    solicitud.save()

    messages.success(request, f"Solicitud de {solicitud.estudiante.nombre} aceptada.")

    
    return redirect('tutoria:solicitudesprof', user_id=request.user.id)

def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    # Solo el tutor correspondiente puede rechazar
    if solicitud.tutor.usuario != request.user:
        messages.error(request, "No tienes permisos para rechazar esta solicitud.")
        return redirect('tutoria:solicitudesprof', user_id=request.user.id)

    solicitud.estado = "Rechazada"
    solicitud.save()

    messages.success(request, f"Solicitud de {solicitud.estudiante.nombre} rechazada.")
    return redirect('tutoria:solicitudesprof', user_id=request.user.id)

def gestortutorias(request):
    
    return render(request, 'tutoria/gestortutorias.html',)

def perfil(request):
    
    return render(request, 'tutoria/perfil.html',)

def perfilusuario(request):
    
    return render(request, 'tutoria/perfilusuario.html',)