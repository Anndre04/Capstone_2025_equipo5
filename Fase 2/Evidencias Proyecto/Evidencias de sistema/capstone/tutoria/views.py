import json
import logging
from django.conf import settings
from django.db import transaction
from django.forms import ValidationError
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Anuncio, ComentarioPredefinido, TipoSolicitud, Solicitud, Usuario, Tutor, TutorArea, Disponibilidad, Archivo, Tutoria, ReseñaTutor  
from .forms import TutorRegistrationForm
from autenticacion.models import AreaInteres, Rol
from notificaciones.services import NotificationService
import uuid
from google.cloud import storage

logger = logging.getLogger(__name__)


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



def subir_archivo_gcp(archivo, tutor_id, tutoria_id=None):
    """
    Sube un archivo a GCP, forzando la lectura binaria completa.
    Esto resuelve el problema de los archivos subidos con 0 bytes.
    """
    GCP_CLIENT = storage.Client.from_service_account_json(
        settings.GOOGLE_APPLICATION_CREDENTIALS
    )

    # 2. Obtener el objeto Bucket (GCP_BUCKET) que tiene los métodos
    GCP_BUCKET = GCP_CLIENT.get_bucket(settings.GOOGLE_CLOUD_BUCKET)

    # 1. Preparar metadata y ruta relativa
    file_uuid = uuid.uuid4().hex[:8] 
    nombre_base = archivo.name.replace(' ', '_')
    ruta_base = f"PDFs/certificados/tutor_{tutor_id}"
    ruta_relativa_gcp = f"{ruta_base}/{file_uuid}_{nombre_base}"
    
    try:
        blob = GCP_BUCKET.blob(ruta_relativa_gcp)
    except NameError:
        logger.error("GCP_BUCKET no está inicializado o accesible.")
        raise RuntimeError("Configuración de GCP faltante.")

    try:
        # ⭐ PASO 1: Mover el puntero al inicio (necesario si ya fue leído)
        archivo.seek(0)
        
        # ⭐ PASO 2: Leer el contenido binario COMPLETO
        contenido_archivo_binario = archivo.read() 
        
        # ⭐ PASO 3: Subir el contenido binario usando upload_from_string
        blob.upload_from_string(
            contenido_archivo_binario, 
            content_type=archivo.content_type
        )
        
        logger.info(f"Subida exitosa: {ruta_relativa_gcp}")
        return ruta_relativa_gcp
        
    except Exception as e:
        logger.error(f"Fallo al subir el archivo {archivo.name} a GCP: {e}", exc_info=True)
        raise RuntimeError(f"Fallo fatal en la subida a GCP: {e}")
    

@login_required
def registrotutor(request):
    user = request.user
    logger.debug(f"Usuario logueado: {user.nombre} (ID: {user.id})")

    # Evita registro duplicado
    if hasattr(user, 'tutor'):
        logger.warning(f"Intento de registro duplicado para usuario: {user.id}")
        messages.warning(request, "Ya estás registrado como tutor.")
        return redirect('home')

    form = TutorRegistrationForm(request.POST or None)

    if request.method == 'POST':
        logger.debug("--- INICIO POST REGISTROTUTOR ---")

        archivos_certificacion = request.FILES.getlist('certificacion')
        logger.debug(f"Archivos 'certificacion' recibidos: {len(archivos_certificacion)}")

        if not form.is_valid():
            logger.warning(f"Formulario NO válido. Errores: {form.errors}")
            messages.error(request, "Hubo errores en el formulario. Revisa las áreas seleccionadas.")
            return render(request, 'tutoria/registrotutor.html', {'form': form})

        try:
            with transaction.atomic():
                # 1️⃣ Crear tutor
                tutor = Tutor.objects.create(
                    usuario=request.user,
                    estado="Pendiente"
                )
                logger.info(f"Tutor creado con ID: {tutor.id}")

                # 2️⃣ Asignar áreas de conocimiento
                for area_id in form.cleaned_data['areas']:
                    TutorArea.objects.create(tutor=tutor, area_id=area_id)
                logger.info(f"Áreas asignadas: {form.cleaned_data['areas']}")

                # 3️⃣ Subir archivos a GCP
                if archivos_certificacion:
                    logger.info(f"Subiendo {len(archivos_certificacion)} certificaciones a GCP.")
                    for archivo_subido in archivos_certificacion:
                        ruta_relativa = subir_archivo_gcp(
                            archivo=archivo_subido,
                            tutor_id=tutor.id
                        )

                        Archivo.objects.create(
                            tutor=tutor,
                            contenido=ruta_relativa,
                            nombre=archivo_subido.name
                        )
                        logger.info(f"Archivo '{archivo_subido.name}' subido exitosamente.")
                else:
                    logger.info("No se recibieron archivos de certificación (campo opcional).")

            rol_tutor = Rol.objects.get(nombre="Tutor")
            user.roles.add(rol_tutor)

            messages.success(request, "Registro completado exitosamente.")
            return redirect('home')

        except Exception as e:
            logger.error(f"Error durante el registro o subida a GCP: {e}", exc_info=True)
            messages.error(request, f"Ocurrió un error durante el proceso: {e}")

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
            return JsonResponse({"success": False, "error": "Faltan datos"}, status=400)

        anuncio = get_object_or_404(Anuncio, id=anuncio_id)
        alumno = get_object_or_404(Usuario, id=alumno_id)

        # Tipo de solicitud "Tutoria"
        tipo, _ = TipoSolicitud.objects.get_or_create(nombre="Tutoria")

        solicitud = Solicitud(
            usuarioenvia=request.user,  # tutor
            usuarioreceive=alumno,
            tipo=tipo,
            mensaje=f"{request.user.nombre} te ha enviado una solicitud de tutoría.",
            estado="Pendiente",
            anuncio=anuncio
        )

        # Validación de tutoría activa
        try:
            solicitud.clean()
        except ValidationError as ve:
            return JsonResponse({"success": False, "error": ve.message}, status=400)

        solicitud.save()

        NotificationService.crear_notificacion(
            usuario=alumno,
            codigo_tipo="Solicitud_tutoria",
            titulo="Nueva solicitud de tutoría",
            mensaje=f"{request.user.nombre} {request.user.p_apellido} te ha enviado una solicitud para iniciar una tutoría.",
            datos_extra={
                "solicitud_id": str(solicitud.id),
                "rol_requerido": "Estudiante",
                }
        )

        return JsonResponse({"success": True, "solicitud_id": str(solicitud.id)})
    
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
def estado_solicitud_tutoria(request, solicitud_id):
    """
    Devuelve el estado actual de una solicitud de tutoría.
    """
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    # Solo el tutor que envió la solicitud puede consultar su estado
    if solicitud.usuarioenvia != request.user:
        return JsonResponse({"error": "No tienes permisos para ver esta solicitud."}, status=403)

    data = {"estado": solicitud.estado}

    # Agregar tutoria_id si la solicitud es aceptada y existe al menos una tutoría creada
    if solicitud.estado == "Aceptada":
        tutoria = solicitud.tutoria_creada.first()  # toma la primera tutoría asociada
        if tutoria:
            data["tutoria_id"] = str(tutoria.id)

    return JsonResponse(data)


@login_required
def tutoria(request, tutoria_id):
    tutoria = get_object_or_404(Tutoria, id=tutoria_id)
    c = ComentarioPredefinido.objects.all

    # Validar que el usuario sea parte de la tutoría
    if request.user != tutoria.solicitud.usuarioenvia and request.user != tutoria.solicitud.usuarioreceive:
        messages.error(request, "No tienes permisos para ver esta tutoría.")
        return redirect('home')

    contexto = {
        'tutoria': tutoria,
        'c' : c
    }

    return render(request, 'tutoria/tutoria.html', contexto)

@login_required
def estado_tutoria(request, tutoria_id):
    """
    Devuelve el estado actual de una tutoría.
    """
    tutoria = get_object_or_404(Tutoria, id=tutoria_id)

    # Solo los involucrados (tutor o estudiante) pueden consultar
    if request.user != tutoria.estudiante and request.user != tutoria.tutor.usuario:
        return JsonResponse({"error": "No tienes permisos para ver esta tutoría."}, status=403)

    return JsonResponse({
        "estado": tutoria.estado,
        "fecha": str(tutoria.fecha),           # YYYY-MM-DD
        "hora_inicio": str(tutoria.hora_inicio), # HH:MM:SS
        "hora_fin": str(tutoria.hora_fin)      # HH:MM:SS
    })

@login_required
def tutoria_completada(request, tutoria_id):
    """
    Marca una tutoría como completada y devuelve información para mostrar reseña opcional.
    """
    tutoria = get_object_or_404(Tutoria, id=tutoria_id)

    # Validar que solo tutor o estudiante puedan completar
    if request.user != tutoria.tutor.usuario and request.user != tutoria.estudiante:
        return JsonResponse({"error": "No tienes permisos"}, status=403)

    # Marcar como completada
    tutoria.estado = "Completada"
    tutoria.save()

    # Devolver info para mostrar modal de reseña
    return JsonResponse({
        "success": True,
        "tutoria_id": str(tutoria.id),
        "estudiante_id": str(tutoria.estudiante.id),
        "tutor_id": str(tutoria.tutor.id),
    })

@login_required
def crear_reseña(request, tutoria_id):
    tutoria = get_object_or_404(Tutoria, id=tutoria_id)


    # Solo el estudiante puede dejar reseña
    if request.user != tutoria.estudiante:
        return JsonResponse({"error": "No tienes permisos"}, status=403)

    if request.method == "POST":
        estrellas = int(request.POST.get("estrellas", 5))
        comentarios_ids = request.POST.getlist("comentarios[]")  # Lista de UUIDs de ComentarioPredefinido

        reseña, created = ReseñaTutor.objects.get_or_create(
            tutoria=tutoria,
            defaults={"estrellas": estrellas}
        )
        reseña.estrellas = estrellas
        if comentarios_ids:
            reseña.comentarios.set(ComentarioPredefinido.objects.filter(id__in=comentarios_ids))
        reseña.save()

        return JsonResponse({"success": True, "reseña_id": str(reseña.id)})