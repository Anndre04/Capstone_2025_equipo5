import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Anuncio, TipoSolicitud, Solicitud, Usuario, Tutor, TutorArea, Disponibilidad, Archivo
from .forms import TutorRegistrationForm
from autenticacion.models import AreaInteres, Rol
from notificaciones.services import NotificationService

dias_semana = [d[0] for d in Disponibilidad.DIAS_SEMANA]

@login_required
def misanunciosprof(request, user_id):
    # Obtener el tutor logueado
    tutor = get_object_or_404(Tutor, usuario=request.user)

    # Anuncios del tutor
    anuncios = Anuncio.objects.filter(tutor=tutor)

    # Preparar disponibilidades por anuncio
    anuncios_disponibilidades = {}
    for anuncio in anuncios:
        disponibilidades = []
        for dia in dias_semana:
            disp = Disponibilidad.objects.filter(anuncio=anuncio, dia=dia).first()
            if disp:
                disponibilidades.append(disp)
        anuncios_disponibilidades[anuncio.id] = disponibilidades

    # Áreas del tutor
    areastutor = TutorArea.objects.filter(tutor=tutor)

    contexto = {
        "anuncios": anuncios,
        "areastutor": areastutor,
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
    if anuncio.tutor.usuario == request.user:
        messages.error(request, "No puedes enviarte una solicitud a ti mismo.")
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

    # Buscar solicitudes existentes que NO estén canceladas ni rechazadas
    solicitud_existente = Solicitud.objects.filter(
        usuarioenvia=request.user,
        usuarioreceive=anuncio.tutor.usuario
    ).exclude(estado__in=["Cancelada", "Rechazada"]).first()

    if solicitud_existente:
        messages.error(request, "Ya tienes una solicitud activa para este tutor.")
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

    # Crear nueva solicitud
    tipo, _ = TipoSolicitud.objects.get_or_create(nombre="Alumno")
    mensaje = request.POST.get("mensaje", "").strip()

    Solicitud.objects.create(
        usuarioenvia=request.user,
        usuarioreceive=anuncio.tutor.usuario,
        tipo=tipo,
        mensaje=mensaje,
        anuncio=anuncio,
        estado="Pendiente"
    )

    messages.success(request, "Solicitud enviada correctamente.")
    return redirect('solicitudesusuario', user_id=request.user.id)

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

@login_required
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

@login_required
def gestortutorias(request, user_id):
    solicitudes = Solicitud.objects.filter(
        usuarioreceive__id=user_id,
        tipo__nombre='Alumno',
        estado='Aceptada'
    )

    context = {
        'solicitudes': solicitudes
    }
    
    return render(request, 'tutoria/gestortutorias.html', context)

@login_required
def obtener_alumnos_anuncio(request, anuncio_id):
    try:
        # Filtrar solicitudes aprobadas del anuncio
        solicitudes = Solicitud.objects.filter(
            anuncio_id=anuncio_id,
            estado="Aceptada",
            tipo__nombre="Alumno"
        ).select_related("usuarioenvia")

        alumnos = [
            {
                "id": s.usuarioenvia.id,
                "nombre": s.usuarioenvia.nombre,
                "p_apellido": s.usuarioenvia.p_apellido,
                "s_apellido": s.usuarioenvia.s_apellido,
                "email": s.usuarioenvia.email
            }
            for s in solicitudes
            if s.usuarioenvia
        ]

        return JsonResponse({"alumnos": alumnos}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@login_required
def perfiltutor(request, tutor_id):

    tutor = get_object_or_404(Tutor, id=tutor_id)

    contexto = {
        'tutor' : tutor
    }
    
    return render(request, 'tutoria/perfiltutor.html', contexto)

@login_required
def registrotutor(request):
    user = request.user
    print(f"[DEBUG] Usuario logueado: {user}")

    # Evitar registro duplicado
    if hasattr(user, 'tutor'):
        print("[DEBUG] Ya existe un tutor para este usuario")
        messages.warning(request, "Ya estás registrado como tutor")
        return render(request, 'tutoria/registrotutor.html', {'form': None})

    # Crear instancia del formulario
    form = TutorRegistrationForm(request.POST or None, request.FILES or None)
    print(f"[DEBUG] request.method: {request.method}")
    print(f"[DEBUG] Archivos subidos: {request.FILES}")

    if request.method == 'POST':
        print(f"[DEBUG] Form data: {request.POST}")
        if form.is_valid():
            print("[DEBUG] Formulario válido")

            # 1️⃣ Crear tutor
            tutor = Tutor.objects.create(
                usuario=user,
                estado='Activo'
            )
            print(f"[DEBUG] Tutor creado: {tutor}")

            try:
                rol_tutor = Rol.objects.get(nombre="Tutor")
                user.roles.add(rol_tutor)
            except Rol.DoesNotExist:
                print("No existe el rol")

            # 2️⃣ Asociar áreas seleccionadas
            areas_ids = form.cleaned_data['areas']
            print(f"[DEBUG] Áreas seleccionadas: {areas_ids}")
            for area_id in areas_ids:
                area = AreaInteres.objects.get(id=area_id)
                TutorArea.objects.create(tutor=tutor, area=area)
                print(f"[DEBUG] Área asociada: {area.nombre}")

            # 3️⃣ Guardar PDF (solo uno)
            archivo = form.cleaned_data.get('certificacion')
            if archivo:
                Archivo.objects.create(
                    nombre=archivo.name,
                    contenido=archivo.read(),
                    tutor=tutor,
                    estado='Pendiente'
                )
                print(f"[DEBUG] Archivo guardado: {archivo.name}")

            messages.success(request, "Registro exitoso")
        else:
            print(f"[DEBUG] Formulario NO válido: {form.errors}")

    return render(request, 'tutoria/registrotutor.html', {'form': form})

@login_required
def crear_solicitud_tutoria(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
    
    try:
        data = json.loads(request.body)
        anuncio_id = data.get("anuncio_id")
        alumno_id = data.get("alumno_id")

        if not anuncio_id or not alumno_id:
            return JsonResponse({"success": False, "error": "Faltan datos"})

        anuncio = get_object_or_404(Anuncio, id=anuncio_id)
        alumno = get_object_or_404(Usuario, id=alumno_id)

        # Obtener el tipo de solicitud "Tutoria" (o crear si no existe)
        tipo, _ = TipoSolicitud.objects.get_or_create(nombre="Tutoria")

        solicitud = Solicitud.objects.create(
            usuarioenvia=request.user,  # tutor
            usuarioreceive=alumno,
            tipo=tipo,
            mensaje=f"{request.user.nombre} te ha enviado una solicitud de tutoría.",
            estado="Pendiente",
            anuncio=anuncio
        )

        # 🔹 Solo enviar notificación si el alumno tiene rol activo "estudiante"
        if alumno.session.get('rol_actual') == "estudiante":
            NotificationService.crear_notificacion(
                usuario=alumno,
                codigo_tipo="solicitud_recibida",
                titulo="Nueva solicitud de tutoría",
                mensaje=f"{request.user.nombre} te ha enviado una solicitud de tutoría.",
                datos_extra={
                    "solicitud_id": solicitud.id,
                    "url": f"tutoria/solicitudes/{solicitud.id}/"
                }
            )

        return JsonResponse({"success": True, "solicitud_id": solicitud.id})
    
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})