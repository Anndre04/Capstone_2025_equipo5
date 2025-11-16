from datetime import datetime, timedelta
from django.utils import timezone
import json
import logging
import mimetypes
import os
from django.db.models import Q
from django.conf import settings
from django.db import DatabaseError, transaction
from django.db.models import Prefetch
from django.forms import ValidationError
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from uuid import UUID
from chat.models import Chat, Mensaje
from evaluaciones.models import Evaluacion, Realizacion
from .models import Anuncio, ComentarioPredefinido, TipoSolicitud, Solicitud, Usuario, Tutor, TutorArea, Disponibilidad, Archivo, Tutoria, ReseñaTutor  
from .forms import TutorRegistrationForm
from autenticacion.models import AreaInteres, Rol
from notificaciones.services import NotificationService
import uuid
from google.cloud import storage
from services.gcp import subir_archivo_gcp

logger = logging.getLogger(__name__)

dias_semana = [d[0] for d in Disponibilidad.DIAS_SEMANA]

@login_required
def descargar_archivo(request, archivo_id):
    
    # 1. Recuperar el objeto Archivo (para validaciones y Foreign Keys)
    archivo = get_object_or_404(Archivo, id=archivo_id)
    
    # 2. 🚨 PASO CRÍTICO: Recuperar el valor 'contenido' explícitamente usando .values()
    # Esto aísla el valor del error de tipado que afecta a 'archivo.contenido'.
    
    # Usamos .values() en un QuerySet filtrado por el ID para obtener el diccionario
    ruta_data = Archivo.objects.filter(id=archivo_id).values('url').first()
    ruta_gcs = str(ruta_data['url']) # 👈 Forzar la limpieza de la cadena
    
    if not ruta_data:
        messages.error(request, "Archivo no encontrado para descarga.")
        return redirect('home')

    # 3. Extraer y asegurar que sea una cadena
    ruta_gcs = str(ruta_data['url'])

    # Llamada a la función de utilidad
    url_descarga = generar_url_firmada_gcs(ruta_gcs, descargar=True)
    
    if url_descarga:
        return redirect(url_descarga)
    else:
        messages.error(request, "Error al generar el enlace de descarga.")
        # Reemplaza 'nombre_real_de_tu_url' con el nombre correcto
        # return redirect('nombre_real_de_tu_url', tutoria_id=archivo.tutoria.id) 
        return redirect('home')

@login_required
def misanunciosprof(request, user_id):

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

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

    return render(request, "tutoria/misanunciosprof.html", contexto)

@login_required
def estadoanuncio(request, anuncio_id):

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

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
        action_message = "activado"
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

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

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

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

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

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')
    
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

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

    DIAS_SEMANA_ORDENADA = [
        ("Lunes", "Lunes"),
        ("Martes", "Martes"),
        ("Miércoles", "Miércoles"),
        ("Jueves", "Jueves"),
        ("Viernes", "Viernes"),
        ("Sábado", "Sábado"),
        ("Domingo", "Domingo"),
    ]

    anuncio = get_object_or_404(Anuncio, id=anuncio_id)
    # Obtener todas las disponibilidades asociadas al anuncio
    disponibilidad = anuncio.disponibilidad_set.all()

    # Opcional: Crear un mapa de disponibilidad para facilitar la visualización en la plantilla
    disponibilidad_map = {
        d.dia: {'mañana': d.mañana, 'tarde': d.tarde, 'noche': d.noche}
        for d in disponibilidad
    }

    contexto = {
        "anuncio": anuncio,
        "disponibilidad_map": disponibilidad_map,
        "dias_ordenados": DIAS_SEMANA_ORDENADA,
    }
    return render(request, 'tutoria/anunciotutor.html', contexto)

@login_required
def enviar_solicitud(request, anuncio_id):

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

    # Obtener anuncio
    anuncio = get_object_or_404(Anuncio, id=anuncio_id)

    # Solo procesar POST
    if request.method != "POST":
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

    # Validar que no se envíe solicitud a sí mismo
    if anuncio.tutor.usuario == request.user:
        messages.error(request, "No puedes enviarte una solicitud a ti mismo.")
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)
    
    tipo = TipoSolicitud.objects.get(nombre="Alumno")

    # Buscar solicitudes existentes que NO estén canceladas ni rechazadas
    solicitud_existente = Solicitud.objects.filter(
        usuarioenvia=request.user,
        usuarioreceive=anuncio.tutor.usuario,
        tipo = tipo,
        anuncio = anuncio
    ).exclude(estado__in=["Cancelada", "Rechazada"]).first()

    if solicitud_existente:
        messages.error(request, "Ya tienes una solicitud activa para este tutor.")
        logger.error(solicitud_existente)
        return redirect('tutoria:anunciotutor', anuncio_id=anuncio.id)

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

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

    # Obtener el tutor
    usuario = get_object_or_404(Usuario, id=user_id)

    tipo = TipoSolicitud.objects.get(nombre="Alumno")
    
    solicitudes = Solicitud.objects.filter(usuarioreceive=usuario, tipo=tipo)

    solicitudes_pendientes = [s for s in solicitudes if s.estado == 'Pendiente']
    
    contexto = {
        'solicitudes': solicitudes,
        'pendientes' : solicitudes_pendientes
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
def gestortutorias(request):
    """
    Obtiene los anuncios únicos asociados a solicitudes aceptadas
    donde el usuario actual (tutor) es el receptor.
    Permite filtrar tutorías por estudiante, anuncio y fecha.
    """

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')
    
    try:
        # 1️⃣ Obtener IDs de anuncios únicos donde el usuario actual es tutor
        anuncio_ids = Solicitud.objects.filter(
            usuarioreceive=request.user,
            tipo__nombre='Alumno',
            estado='Aceptada',
            anuncio__isnull=False
        ).values_list('anuncio__id', flat=True).distinct()

        # 2️⃣ Obtener los anuncios activos basados en esos IDs
        anuncios = Anuncio.objects.filter(
            id__in=anuncio_ids,
            estado="Activo"
        ).order_by('titulo')

        # 3️⃣ Obtener alumnos con sus tutorías, evaluaciones y archivos
        alumnos = Usuario.objects.filter(
            solicitudes__estado="Aceptada",
            solicitudes__tipo__nombre="Alumno"
        ).prefetch_related(
            "tutorias_recibidas",  # Tutorías del alumno
            "realizaciones",       # Evaluaciones realizadas por el alumno
            "tutorias_recibidas__archivos"  # Archivos de las tutorías
        ).distinct()

        alumnos_info = []

        for alumno in alumnos:
            tutorias = alumno.tutorias_recibidas.all()
            archivos_count = sum(t.archivos.count() for t in tutorias)
            realizaciones_count = alumno.realizaciones.count()
            
            alumnos_info.append({
                'alumno': alumno,
                'tutorias_count': tutorias.count(),
                'archivos_count': archivos_count,
                'realizaciones_count': realizaciones_count,
            })

        # 3️⃣ Si el usuario es tutor, obtener sus tutorías
        
        tutorias = (
            Tutoria.objects
            .filter(tutor=request.user.tutor)
            .select_related('anuncio', 'estudiante')
            .order_by('-fecha_creacion')
        )

        # --- FILTROS DEL BUSCADOR ---
        estudiante_query = request.GET.get('estudiante', '').strip()
        anuncio_id = request.GET.get('anuncio', '').strip()
        fecha_query = request.GET.get('fecha', '').strip()

        # 🔍 Filtro por nombre del estudiante
        if estudiante_query:
            tutorias = tutorias.filter(
                Q(estudiante__nombre__icontains=estudiante_query) |
                Q(estudiante__p_apellido__icontains=estudiante_query)
            )

        # 🔍 Filtro por anuncio seleccionado
        if anuncio_id:
            tutorias = tutorias.filter(anuncio_id=anuncio_id)

        # 🔍 Filtro por fecha exacta
        if fecha_query:
            try:
                fecha_dt = datetime.strptime(fecha_query, '%Y-%m-%d').date()
                tutorias = tutorias.filter(fecha_creacion__date=fecha_dt)
            except ValueError:
                messages.warning(request, "Formato de fecha inválido.")

        # 🔹 Anuncios únicos (para select del filtro)
        anuncios_unicos = (
            Tutoria.objects
            .filter(tutor=request.user.tutor)
            .select_related('anuncio')
            .order_by('anuncio_id')
            .distinct('anuncio_id')
        )

    except DatabaseError as e:
        logger.error(f"Error en gestor de tutorías: {e}")
        messages.error(request, "Hubo un error al cargar tus tutorías.")
        return redirect('home')

    context = {
        'anuncios': anuncios,
        'tutorias': tutorias,
        'anuncios_unicos': anuncios_unicos,
        'alumnos_info': alumnos_info,
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

    if not hasattr(request.user, 'tutor'):
        logger.error("No tiene permisos correspondientes")
        return redirect('home')

    tutor = get_object_or_404(Tutor, id=tutor_id)

    contexto = {
        'tutor' : tutor
    }
    
    return render(request, 'tutoria/perfiltutor.html', contexto)


@login_required
def registrotutor(request):
    user = request.user
    logger.debug(f"Usuario logueado: {user.nombre} (ID: {user.id})")

    # Si ya es tutor activo → no permitir registro
    if hasattr(user, 'tutor') and user.tutor.estado == Tutor.EstadoTutor.ACTIVO:
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

                # ------------------------------------------
                # 1️⃣ Crear o reactivar tutor
                # ------------------------------------------
                if hasattr(user, 'tutor'):
                    tutor = Tutor.objects.select_for_update().get(pk=user.tutor.id)
                    tutor.estado = Tutor.EstadoTutor.ACTIVO
                    tutor.save()
                else:
                    tutor = Tutor.objects.create(
                        usuario=user,
                        estado=Tutor.EstadoTutor.ACTIVO
                    )

                areas_seleccionadas = request.POST.getlist("areas")

            if not areas_seleccionadas:
                raise Exception("Debe seleccionar al menos un área.")

            # Desactivar áreas antiguas NO seleccionadas
            TutorArea.objects.filter(tutor=tutor).exclude(
                area_id__in=areas_seleccionadas
            ).update(
                activo=False,
                fecha_desactivado=timezone.now()
            )

            # Crear o reactivar áreas seleccionadas
            for area_id in areas_seleccionadas:

                area = AreaInteres.objects.get(id=area_id)

                relacion, creada = TutorArea.objects.get_or_create(
                    tutor=tutor,
                    area=area,
                    defaults={"activo": True}
                )

                # Reactivar si existía pero estaba desactivada
                if not creada and not relacion.activo:
                    relacion.activo = True
                    relacion.fecha_desactivado = None
                    relacion.save()

                # ------------------------------------------
                # 3️⃣ Subida de certificaciones a GCP
                # ------------------------------------------
                if archivos_certificacion:
                    logger.info(f"Subiendo {len(archivos_certificacion)} certificaciones a GCP.")
                    
                    for i, archivo_subido in enumerate(archivos_certificacion):

                        nombre_personalizado = request.POST.get(
                            f'nombre_archivo_{i}',
                            archivo_subido.name
                        )

                        ruta_relativa = subir_archivo_gcp(
                            archivo=archivo_subido,
                            tutor_id=tutor.id,
                            tutoria_id=None
                        )

                        if not ruta_relativa:
                            messages.error(request, f"Falló la subida del archivo '{nombre_personalizado}'. Se revertirá el registro.")
                            raise Exception("Error en la subida a GCP.")

                        Archivo.objects.create(
                            tutor=tutor,
                            url=ruta_relativa,
                            nombre=nombre_personalizado
                        )
                else:
                    logger.info("No se recibieron archivos de certificación (campo opcional).")

                # ------------------------------------------
                # 4️⃣ Asignar rol Tutor si no lo tiene
                # ------------------------------------------
                rol_tutor = Rol.objects.get(nombre="Tutor")
                if not user.roles.filter(id=rol_tutor.id).exists():
                    user.roles.add(rol_tutor)

                messages.success(request, "Registro completado exitosamente. Está pendiente de aprobación.")
                return redirect('home')

        except Exception as e:
            logger.error(f"Error durante el registro o subida a GCP: {e}", exc_info=True)
            if not messages.get_messages(request):
                messages.error(request, f"Ocurrió un error inesperado. Intenta de nuevo.")
            return render(request, 'tutoria/registrotutor.html', {'form': form})

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

        return JsonResponse({ "mensaje": "Solicitud enviada.", "tipo": "success", "solicitud_id": solicitud.id})
    
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

    # Usuarios de la conversación
    u1 = tutoria.solicitud.usuarioenvia
    u2 = tutoria.solicitud.usuarioreceive

    # Buscar si YA existe un chat creado entre ellos
    chat = Chat.objects.filter(users=u1).filter(users=u2).first()

    # Si no existe, lo creas
    if not chat:
        chat = Chat.objects.create(
            nombre=f"Chat tutoria {tutoria_id}",
            estado="activo"
        )
        chat.users.add(u1, u2)
        chat.save()

    # Traer los mensajes del chat
    mensajes = Mensaje.objects.filter(chat=chat).order_by("timestamp")

    contexto = {
        "tutoria": tutoria,
        "chat_id": chat.id,
        "mensajes": mensajes
    }

    return render(request, "tutoria/tutoria.html", contexto)


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

@login_required
def archivos_tutoria(request, tutoria_id):
    """
    Maneja la visualización (GET) y subida de archivos (POST vía AJAX)
    relacionados con una tutoría específica.
    """
    # 1. Obtener la tutoría y validar permisos
    try:
        tutoria = get_object_or_404(Tutoria, id=tutoria_id)
        # Asume que tu modelo Tutoría tiene un FK a Tutor (tutor.usuario) y Estudiante (estudiante.usuario)
        if request.user != tutoria.tutor.usuario and request.user != tutoria.estudiante.usuario:
            # Si no es ni tutor ni estudiante de la tutoría, acceso denegado.
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Si es AJAX, devuelve JSON
                return JsonResponse({'error': 'No tienes permiso para acceder a esta tutoría.'}, status=403)
            else:
                # Si es petición normal (GET), redirige
                messages.error(request, "No tienes permiso para ver los archivos de esta tutoría.")
                return redirect('home') 

    except Exception:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Tutoría no encontrada.'}, status=404)
        else:
            messages.error(request, "La tutoría solicitada no existe o no es accesible.")
            return redirect('url_a_historial') 


    # --- LÓGICA POST (Subida de Archivos vía AJAX) ---
    if request.method == 'POST':
        logger.debug(f"--- INICIO POST ARCHIVOS TUTORÍA {tutoria_id} (AJAX) ---")
        
        archivos_subidos = request.FILES.getlist('archivo')
        
        if not archivos_subidos:
            return JsonResponse({'error': 'No se seleccionó ningún archivo para subir.'}, status=400)

        try:
            with transaction.atomic():
                archivos_guardados_count = 0

                for i, archivo_subido in enumerate(archivos_subidos):
                    
                    # 🔑 Obtener el nombre personalizado desde el POST
                    nombre_personalizado = request.POST.get(f'nombre_archivo_{i}', archivo_subido.name)
                    
                    # 📞 LLAMADA A LA FUNCIÓN DE GCS con tutoria_id
                    ruta_relativa = subir_archivo_gcp(
                        archivo=archivo_subido,
                        tutoria_id=tutoria.id, # Usamos el ID de la tutoría para la ruta GCS
                        tutor_id=None          
                    )

                    logger.error(ruta_relativa)

                    if ruta_relativa:
                        # 💾 Crear el objeto Archivo en la base de datos
                        Archivo.objects.create(
                            tutoria=tutoria,
                            url=ruta_relativa,
                            nombre=nombre_personalizado
                        )
                        archivos_guardados_count += 1
                        logger.info(f"Archivo de tutoría '{nombre_personalizado}' subido a GCS: {ruta_relativa}")
                    else:
                        # Si la subida a GCS falla, lanzamos excepción para revertir la transacción.
                        logger.error(f"Fallo crítico de subida a GCS para el archivo: {archivo_subido.name}. Revirtiendo.")
                        raise Exception("Error en la subida a GCP. Transacción revertida.")
                
                # 2. Éxito: Devolver JSON
                return JsonResponse({
                    'success': True, 
                    'message': f'Se subieron {archivos_guardados_count} archivos correctamente.',
                    'files_uploaded': archivos_guardados_count
                })

        except Exception as e:
            logger.error(f"Error AJAX durante la subida de archivos de tutoría {tutoria_id}: {e}", exc_info=True)
            # 3. Error: Devolver JSON con estado 500
            return JsonResponse({'error': f'Error interno: {e}. La subida fue revertida.'}, status=500)


    # --- LÓGICA GET (Visualización de Archivos - Petición Normal) ---
    # Esto se ejecuta si la página se accede por URL directamente, no por AJAX.
    
    archivos_asociados = Archivo.objects.filter(tutoria=tutoria).order_by('-fecha_subida')

    context = {
        'tutoria': tutoria,
        'archivos': archivos_asociados,
        # Si necesitas el formulario del modal, asegúrate de que el modal HTML esté en el template
    }
    
    return render(request, 'tutoria/detalle_tutoria.html', context)

@login_required
def detalle_tutoria(request, tutoria_id):

    tutoria = get_object_or_404(Tutoria, id=tutoria_id)

    duracion = tutoria.hora_fin - tutoria.hora_inicio
    # Convertir a minutos
    minutos = int(duracion.total_seconds() / 60)
    tutoria.duracion_minutos = minutos

    contexto = {
        'tutoria': tutoria
    }

    return render(request, 'tutoria/detalle_tutoria.html', contexto)