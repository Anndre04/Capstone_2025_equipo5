from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Anuncio, TipoSolicitud, Solicitud, Usuario, Tutor, TutorArea, Disponibilidad

@login_required
def misanunciosprof(request, user_id):
    """
    Vista que muestra los anuncios activos de un tutor.
    """
    tutor = get_object_or_404(Tutor, usuario__id=user_id)
    areastutor = TutorArea.objects.filter(tutor=tutor)
    anuncios = Anuncio.objects.filter(tutor=tutor, activo=True).order_by('-fecha_creacion')

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    contexto = {
        'anuncios': anuncios,
        'areastutor': areastutor,
        'dias_semana': dias_semana,
    }
    return render(request, 'tutoria/mistutoriasprof.html', contexto)

@login_required
def publicartutoria(request, user_id):
    tutor = get_object_or_404(Tutor, usuario__id=user_id)

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        area_id = request.POST.get("area")
        area = get_object_or_404(TutorArea, id=area_id)

        if int(precio) < 5000:
            messages.error(request, "El precio mínimo permitido es $5000")
            return redirect("tutoria:misanunciosprof", user_id=user_id)

        # Validar que no exista un anuncio activo para la misma área
        if Anuncio.objects.filter(tutor=tutor, area=area, activo=True).exists():
            messages.error(request, f"Ya existe un anuncio activo para el área {area}")
            return redirect("tutoria:misanunciosprof", user_id=user_id)

        # Crear el anuncio
        anuncio = Anuncio.objects.create(
            tutor=tutor,
            area=area,
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
        )

        # Guardar la disponibilidad
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        for dia in dias_semana:
            turnos = request.POST.getlist(f"turnos_{dia}[]")  # Esto devuelve una lista como ['M','T']
            
            manana = "M" in turnos
            tarde = "T" in turnos
            noche = "N" in turnos

            print(f"{dia}: Mañana={manana}, Tarde={tarde}, Noche={noche}")

            if manana or tarde or noche:
                Disponibilidad.objects.create(
                    anuncio=anuncio,
                    dia=dia,
                    mañana=manana,
                    tarde=tarde,
                    noche=noche,
                )

        messages.success(request, "Tutoría publicada correctamente")
        return redirect('tutoria:misanunciosprof', user_id=user_id)

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
    usuario = get_object_or_404(Usuario, id=user_id)
    
    solicitudes = Solicitud.objects.filter(usuarioreceive=usuario, estado='Pendiente')
    
    contexto = {
        'solicitudes': solicitudes,
    }
    
    return render(request, 'tutoria/solicitudesprof.html', contexto)

@login_required
def aceptar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    # Solo el tutor correspondiente puede aceptar
    if solicitud.usuarioreceive != request.user:
        messages.error(request, "No tienes permisos para aceptar esta solicitud.")
        return redirect('tutoria:solicitudesprof', user_id=request.user.id)

    solicitud.estado = "Aceptada"
    solicitud.save()

    messages.success(request, f"Solicitud de {solicitud.usuarioenvia.nombre} aceptada.")

    
    return redirect('tutoria:solicitudesprof', user_id=request.user.id)

def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    # Solo el tutor correspondiente puede rechazar
    if solicitud.usuarioreceive != request.user:
        messages.error(request, "No tienes permisos para rechazar esta solicitud.")
        return redirect('tutoria:solicitudesprof', user_id=request.user.id)

    solicitud.estado = "Rechazada"
    solicitud.save()

    messages.success(request, f"Solicitud de {solicitud.usuarioenvia.nombre} rechazada.")
    return redirect('tutoria:solicitudesprof', user_id=request.user.id)

def gestortutorias(request):
    
    return render(request, 'tutoria/gestortutorias.html',)

def perfil(request):
    
    return render(request, 'tutoria/perfil.html',)

def perfilusuario(request):
    
    return render(request, 'tutoria/perfilusuario.html',)