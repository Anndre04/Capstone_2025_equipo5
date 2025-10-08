from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Anuncio, TipoSolicitud, Solicitud, Usuario, Tutor, TutorArea, Disponibilidad

dias_semana = [d[0] for d in Disponibilidad.DIAS_SEMANA]

@login_required
def misanunciosprof(request, user_id):
    anuncios = Anuncio.objects.filter(tutor__usuario=request.user)

    # Preparar disponibilidades por anuncio
    anuncios_disponibilidades = {}
    for anuncio in anuncios:
        disponibilidades = []
        for dia in dias_semana:
            disp = Disponibilidad.objects.filter(anuncio=anuncio, dia=dia).first()
            if disp:
                disponibilidades.append(disp)
        anuncios_disponibilidades[anuncio.id] = disponibilidades


    

    contexto = {
        "anuncios": anuncios,
        "areastutor": TutorArea.objects.all(),
        "dias_semana": dias_semana,
        "anuncios_disponibilidades": anuncios_disponibilidades,
    }

    return render(request, "tutoria/mistutoriasprof.html", contexto)

@login_required
def estadoanuncio(request, anuncio_id):
    # Solo permitir método POST
    if request.method != "POST":
        return redirect('tutoria:misanunciosprof', user_id=request.user.id)

    # Obtener anuncio
    anuncio = get_object_or_404(Anuncio, id=anuncio_id)

    # Validar que solo el tutor dueño pueda cambiarlo
    if anuncio.tutor.usuario != request.user:
        messages.error(request, "No puedes cambiar el estado de un anuncio que no es tuyo.")
        return redirect('tutoria:misanunciosprof', user_id=request.user.id)

    # Cambiar estado en ciclo: Activo -> Deshabilitado -> Eliminado
    if anuncio.estado == "Activo":
        anuncio.estado = "Deshabilitado"
        action_message = "deshabilitado"
    elif anuncio.estado == "Deshabilitado":
        anuncio.estado = "Activo"
        action_message = "Activado"
    else:
        messages.error(request, "Estado de anuncio no válido.")
        return redirect('tutoria:misanunciosprof', user_id=request.user.id)

    anuncio.save()
    messages.success(request, f"Anuncio {action_message} correctamente.")
    
    # Redirigir a la URL de origen o a la vista por defecto
    next_url = request.POST.get('next', 'tutoria:misanunciosprof')
    return redirect(next_url, user_id=request.user.id)

@login_required
def eliminar_anuncio(request, anuncio_id):
    if request.method != "POST":
        return redirect('tutoria:misanunciosprof', user_id=request.user.id)

    anuncio = get_object_or_404(Anuncio, id=anuncio_id)

    if anuncio.tutor.usuario != request.user:
        messages.error(request, "No puedes eliminar un anuncio que no es tuyo.")
        return redirect('tutoria:misanunciosprof', user_id=request.user.id)

    anuncio.estado = "Eliminado"
    anuncio.save()
    messages.success(request, "Anuncio eliminado correctamente.")
    
    next_url = request.POST.get('next', 'tutoria:misanunciosprof')
    return redirect(next_url, user_id=request.user.id)

@login_required
def editaranuncio(request, anuncio_id):
    anuncio = get_object_or_404(Anuncio, id=anuncio_id)

    # Solo el tutor dueño puede editar
    if anuncio.tutor.usuario != request.user:
        messages.error(request, "No puedes editar un anuncio que no es tuyo.")
        return redirect('tutoria:mis_tutorias_prof')

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        precio = request.POST.get("precio", "").strip()
        area_id = request.POST.get("area")
        dias_seleccionados = request.POST.getlist("dias[]")

        if not titulo or not descripcion or not precio or not area_id:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('tutoria:mis_tutorias_prof')

        try:
            precio = int(precio)
        except ValueError:
            messages.error(request, "El precio debe ser un número.")
            return redirect('tutoria:mis_tutorias_prof')

        # Actualizar anuncio
        anuncio.titulo = titulo
        anuncio.descripcion = descripcion
        anuncio.precio = precio
        anuncio.area = get_object_or_404(TutorArea, id=area_id)
        anuncio.save()

        # Actualizar disponibilidad
        Disponibilidad.objects.filter(anuncio=anuncio).delete()
        for dia in dias_seleccionados:
            turnos = request.POST.getlist(f"turnos_{dia}[]")
            Disponibilidad.objects.create(
                anuncio=anuncio,
                dia=dia,
                mañana="M" in turnos,
                tarde="T" in turnos,
                noche="N" in turnos
            )

        messages.success(request, "Anuncio y disponibilidad actualizados correctamente.")
        return redirect('tutoria:misanunciosprof', request.user.id)

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
        if Anuncio.objects.filter(tutor=tutor, area=area, estado__in=['Activo', 'Deshabilitado']).exists():
            messages.error(request, f"Ya existe un anuncio creado para el área {area}")
            return redirect("tutoria:misanunciosprof", user_id=user_id)

        # Crear el anuncio
        anuncio = Anuncio.objects.create(
            tutor=tutor,
            area=area,
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
            estado='Activo'
        )

        # Guardar la disponibilidad
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        for dia in dias_semana:
            turnos = request.POST.getlist(f"turnos_{dia}[]")  # Esto devuelve una lista como ['M','T']
            
            manana = "M" in turnos
            tarde = "T" in turnos
            noche = "N" in turnos

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
    disponibilidad = Disponibilidad.objects.filter(anuncio=anuncio)

    contexto = {
        'anuncio': anuncio,
        'disponibilidad': disponibilidad
    }
    return render(request, 'tutoria/anunciotutor.html', contexto)

@login_required
def enviar_solicitud(request, anuncio_id):
    # Obtener anuncio
    anuncio = get_object_or_404(Anuncio, id=anuncio_id)

    # Solo procesar POST
    if request.method != "POST":
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

    # Validar que no se envíe solicitud a sí mismo
    if anuncio.tutor == request.user:
        messages.error(request, "No puedes enviarte una solicitud a ti mismo.")
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

    # Validar solicitud duplicada
    if Solicitud.objects.filter(usuarioenvia=request.user, anuncio=anuncio).exists():
        messages.error(request, "Ya enviaste una solicitud a este tutor.")
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

    # Crear solicitud
    tipo, _ = TipoSolicitud.objects.get_or_create(nombre="Alumno")
    mensaje = request.POST.get("mensaje", "").strip()
    Solicitud.objects.create(
        usuarioenvia=request.user,
        usuarioreceive=anuncio.tutor.usuario,
        tipo=tipo,
        mensaje=mensaje,
        anuncio=anuncio
    )
    messages.success(request, "Solicitud enviada correctamente.")
    
    return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

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