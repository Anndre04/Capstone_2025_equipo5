from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import logging
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from autenticacion.tasks import BASE_URL
from tutoria.models import Anuncio, Archivo, TipoSolicitud, Tutor, TutorArea, Tutoria
from autenticacion.models import AreaInteres, Comuna, Institucion, Nivel_educacional, Ocupacion, Pais, Region, Usuario, UsuarioArea
from tutoria.models import Anuncio, Solicitud
from django.db.models import Avg, Case, When, Value, IntegerField, Q
from django.contrib.auth import logout
from services.gcp import generar_url_firmada, get_bucket, subir_archivo_gcp


logger = logging.getLogger(__name__)

def home(request):

    try:
        anuncios = Anuncio.objects.filter(
            tutor__usuario__roles__nombre='Tutor',
            tutor__estado='Activo',
            estado='Activo'
        ).select_related('tutor', 'tutor__usuario').distinct()


        areainteres = AreaInteres.objects.all()

        # Obtener filtros del GET
        nombre = request.GET.get('nombre', '')
        precio_max_str = request.GET.get('precio_max', '')  # Usamos _str para manejo inicial
        asignatura_id = request.GET.get('asignatura', '')
        estrellas_min = request.GET.get('estrellas', '')

        # Variables para contexto y aplicación de filtros
        filtros_activos = {}
        
        # 2. Aplicar Filtros Secundarios

        # Filtrar por nombre del tutor
        if nombre:
            anuncios = anuncios.filter(tutor__usuario__nombre__icontains=nombre)
            filtros_activos['nombre'] = nombre

        # Filtrar por precio máximo 🌟 AJUSTE CLAVE AQUÍ 🌟
        if precio_max_str:
            try:
                precio_max = int(precio_max_str)
                # Aplicamos el filtro si la conversión fue exitosa
                anuncios = anuncios.filter(precio__lte=precio_max)
                # Almacenamos el valor original (string) para mantener seleccionado el <select> en el template
                filtros_activos['precio_max'] = precio_max_str 
            except ValueError:
                # Si el valor no es un número (ej: el usuario lo manipula), simplemente lo ignoramos
                logger.warning(f"Valor no numérico para precio_max: {precio_max_str}")
                # No se aplica el filtro, pero tampoco se rompe la página

        # Filtrar por asignatura / área de interés
        if asignatura_id:
            anuncios = anuncios.filter(area__id=asignatura_id)
            filtros_activos['asignatura'] = asignatura_id

        # Filtrar por estrellas mínimas
        if estrellas_min:
            # Convertimos a float/decimal si fuera necesario, o a int si el rating es entero
            estrellas_float = float(estrellas_min) 
            anuncios = anuncios.annotate(
                # Nota: Este annotate es costoso. Es mejor anotar una vez si se usa más.
                promedio_estrellas_anotado=Avg('tutorias__reseña__estrellas')
            ).filter(promedio_estrellas_anotado__gte=estrellas_float)
            filtros_activos['estrellas'] = estrellas_min

        contexto = {
            "anuncios": anuncios,
            "areas": areainteres,
            "filtros": filtros_activos, # Usamos los filtros_activos para el contexto
        }

        return render(request, 'home/home.html', contexto)
    
    except Exception as e:
        messages.error(request, "Hubo un error cargando la página principal. Inténtelo más tarde.")
        logger.error("Error en home view", exc_info=True)
        return redirect("home")

@login_required
def perfilusuario(request):
    usuario = request.user

    contexto = {
        "usuario": usuario,
        "areas": AreaInteres.objects.all(),
        "areas_usuario": usuario.areas_interes,  # QuerySet por tu property
    }

    # Si NO es tutor activo → return inmediato
    if not usuario.es_tutor_activo():
        contexto["es_tutor"] = False
        return render(request, "home/perfilusuario.html", contexto)

    try:
        tutor = Tutor.objects.prefetch_related(
            "areastutor", "certificados"
        ).get(usuario=usuario)

        contexto.update({
            "es_tutor": True,
            "tutor": tutor,
            "areastutor": tutor.areastutor.filter(activo=True),
            "archivos": [
                {
                    "nombre": c.nombre,
                    "estado": c.estado,
                    "url_ver": generar_url_firmada(c.url, descargar=False),
                    "url_descargar": generar_url_firmada(c.url, descargar=True),
                }
                for c in tutor.certificados.all()
            ],
        })

    except Tutor.DoesNotExist:
        contexto["es_tutor"] = False

    except Exception as e:
        messages.error(request, "Hubo un error cargando su perfil. Inténtelo más tarde.")
        logger.error(f"Error cargando perfil: {usuario.id}: {e}", exc_info=True)
        return redirect("home")

    return render(request, "home/perfilusuario.html", contexto)

@login_required
def editarperfil(request):
    usuario = request.user
    tutor = getattr(usuario, "tutor", None)

    areas_usuario_ids = list(usuario.areas_interes.values_list('id', flat=True))
    areastutor_ids = []
    if tutor:
        areastutor_ids = list(
            TutorArea.objects.filter(tutor=tutor, activo=True).values_list('area_id', flat=True)
        )

    areas = AreaInteres.objects.all()

    if request.method == "POST":
        logger.info("POST recibido en editarperfil")

        pais_id = request.POST.get("pais")
        if pais_id:
            try:
                usuario.pais = Pais.objects.get(id=pais_id)
            except Pais.DoesNotExist:
                logger.warning(f"[home.views] Pais con id {pais_id} no existe")

        region_id = request.POST.get("region")
        if region_id:
            try:
                usuario.region = Region.objects.get(id=region_id)
            except Region.DoesNotExist:
                logger.warning(f"[home.views] Region con id {region_id} no existe")

        comuna_id = request.POST.get("comuna")
        if comuna_id:
            try:
                usuario.comuna = Comuna.objects.get(id=comuna_id)
            except Comuna.DoesNotExist:
                logger.warning(f"[home.views] Comuna con id {comuna_id} no existe")

        ocupacion_id = request.POST.get("ocupacion")
        if ocupacion_id:
            try:
                usuario.ocupacion = Ocupacion.objects.get(id=ocupacion_id)
            except Ocupacion.DoesNotExist:
                logger.warning(f"[home.views] Ocupacion con id {ocupacion_id} no existe")

        n_educacion_id = request.POST.get("n_educacion")
        if n_educacion_id:
            try:
                usuario.n_educacion = Nivel_educacional.objects.get(id=n_educacion_id)
            except Nivel_educacional.DoesNotExist:
                logger.warning(f"[home.views] Nivel educacional con id {n_educacion_id} no existe")

        institucion_id = request.POST.get("institucion")
        if institucion_id:
            try:
                usuario.institucion = Institucion.objects.get(id=institucion_id)
            except Institucion.DoesNotExist:
                logger.warning(f"[home.views] Institucion con id {institucion_id} no existe")

        usuario.save()
        logger.info(f"Usuario actualizado: {usuario.nombre} {usuario.p_apellido} {usuario.s_apellido}")

        # Áreas de interés (ManyToMany)
        areas_seleccionadas = request.POST.getlist("areas_interes")
        logger.info(f"Áreas seleccionadas por el usuario: {areas_seleccionadas}")
        if areas_seleccionadas:
            usuario.areas_interes.set(areas_seleccionadas)
        else:
            logger.info("No se recibieron áreas de interés. No se modificarán las existentes.")
        logger.info(f"Áreas de interés actuales: {[a.id for a in usuario.areas_interes.all()]}")

        # Datos del tutor
        if tutor:
            tutor.sobremi = request.POST.get("Sobremi")
            tutor.save()
            logger.info(f"Tutor actualizado: {tutor.sobremi}")

            nuevas_areas = request.POST.getlist("areas_conocimiento")
            logger.info(f"Áreas de conocimiento enviadas: {nuevas_areas}")

            # Desactivar las que no están en la selección
            for area in TutorArea.objects.filter(tutor=tutor):
                if str(area.area_id) not in nuevas_areas:
                    area.activo = False
                    area.save()
                    logger.info(f"Área desactivada: {area.area_id}")
                else:
                    area.activo = True
                    area.save()
                    logger.info(f"Área activada: {area.area_id}")

            # Agregar nuevas si no existían
            for area_id in nuevas_areas:
                obj, created = TutorArea.objects.get_or_create(
                    tutor=tutor, area_id=area_id,
                    defaults={'activo': True}
                )
                if created:
                    logger.info(f"Área nueva creada para tutor: {area_id}")
                else:
                    logger.info(f"Área ya existente, asegurando activo=True: {area_id}")
                    if not obj.activo:
                        obj.activo = True
                        obj.save()

            archivos_a_eliminar = request.POST.get('archivos_eliminar', '')
            if archivos_a_eliminar:
                archivos_a_eliminar = archivos_a_eliminar.split(',')
                bucket = get_bucket()
                for archivo_id in archivos_a_eliminar:
                    try:
                        archivo_obj = Archivo.objects.get(id=archivo_id, tutor=tutor)
                        if archivo_obj.url:
                            blob = bucket.blob(archivo_obj.url)
                            blob.delete()
                            logger.info(f"[home.views] Archivo eliminado en GCP: {archivo_obj.url}")
                    except Archivo.DoesNotExist:
                        logger.warning(f"[home.views] Archivo no encontrado para eliminar: {archivo_id}")

            # --- SUBIR NUEVOS ARCHIVOS ---
            if request.FILES.getlist('certificacion'):
                for f in request.FILES.getlist('certificacion'):
                    ruta_gcs = subir_archivo_gcp(f, nombre=f.name, tutor_id=tutor.id)
                    if ruta_gcs:
                        Archivo.objects.create(
                            tutor=tutor,
                            nombre=f.name,
                            url=ruta_gcs,
                            estado="Pendiente"
                        )
                        logger.info(f"[home.views] Nuevo archivo registrado: {f.name}")

        messages.success(request, "Se ha editado tu perfil exitosamente.")
        return redirect("perfilusuario")

    contexto = {
        "usuario": usuario,
        "tutor": tutor,
        "areas": areas,
        'areas_usuario_ids': areas_usuario_ids,
        "areastutor_ids": areastutor_ids,
        "paises": Pais.objects.all(),
        "regiones": Region.objects.all(),
        "comunas": Comuna.objects.all(),
        "ocupaciones": Ocupacion.objects.all(),
        "niveles": Nivel_educacional.objects.all(),
        "instituciones": Institucion.objects.all(),
        "archivos_tutor": tutor.certificados.all() if tutor else None
    }

    return render(request, 'home/editarperfil.html', contexto)

@login_required
def solicitudesusuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    
    try:

        tipo = TipoSolicitud.objects.get(nombre="Alumno")

        solicitudes = Solicitud.objects.filter(
            usuarioenvia=usuario,
            tipo=tipo,
            estado__in=["Aceptada", "Pendiente", "Rechazada"]
        ).annotate(
            estado_orden=Case(
                When(estado="Pendiente", then=Value(0)),
                When(estado="Rechazada", then=Value(1)),
                When(estado="Aceptada", then=Value(2)),
                output_field=IntegerField(),
            )
        ).order_by("estado_orden")
        
        contexto = {
            'solicitudes': solicitudes,
        }
        
        return render(request, 'home/solicitudesusuario.html', contexto)
    except Exception:
        messages.error(request, "Hubo un error. Intentelo mas tarde")
        logger.error("Error obteniendo las solicitudes del usuario", exc_info=True)
        return redirect("home")

@login_required
def cancelarsolicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
        
    try: 
        
        # Validar que el usuario sea quien la envió
        if solicitud.usuarioenvia != request.user:
            messages.error(request, "No tienes permiso para cancelar esta solicitud.")
            return redirect('home')  # Cambia a tu URL real

        if request.method == 'POST':
            solicitud.estado = "Cancelada"
            solicitud.save()

        messages.success(request, "Solicitud cancelada exitosamente.")
        return redirect('solicitudesusuario', user_id=request.user.id )
    except Exception:
        messages.error(request, "Hubo un error procesando su solicitud")
        logger.error("Error cancelando las solicitudes del usuario", exc_info=True)
        return redirect("solicitudesusuario", request.user.id)

@login_required
def aceptar_solicitud_tutoria(request, solicitud_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    # Solo el usuario receptor puede aceptar
    if solicitud.usuarioreceive != request.user:
        return JsonResponse({"success": False, "error": "No tienes permisos"}, status=403)

    # Marcar la solicitud como aceptada
    solicitud.estado = "Aceptada"
    
    # Validar tutorías activas SOLO si es tipo tutoria
    if solicitud.tipo.nombre.lower() == "tutoria":
        try:
            solicitud.clean()  # lanza ValidationError si hay tutoría activa
        except ValidationError as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    solicitud.save()

    # Solo crear tutoría si es de tipo "tutoria"
    if solicitud.tipo.nombre.lower() == "tutoria":
        dt_inicio = datetime.now()  # o tomar de request.POST si querés fecha personalizada
        dt_fin = dt_inicio + timedelta(seconds=15)

        tutoria = Tutoria.objects.create(
            solicitud=solicitud,
            anuncio=solicitud.anuncio,
            tutor=solicitud.usuarioenvia.tutor,
            estudiante=solicitud.usuarioreceive,
            hora_inicio=dt_inicio,
            hora_fin=dt_fin,   
            estado="En curso"
        )

        url = reverse('tutoria:tutoria', args=[tutoria.id])
        return JsonResponse({"success": True, "redirect_url": url})

    return JsonResponse({"success": True, "info": "Solicitud aceptada, no es tutoría."})

@login_required
def rechazar_solicitud_tutoria(request, solicitud_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    if solicitud.usuarioreceive != request.user:
        return JsonResponse({"success": False, "error": "No tienes permisos"}, status=403)

    solicitud.estado = "Rechazada"
    solicitud.save()
    return JsonResponse({"success": True})

@login_required
def historial_tutoria(request, user_id):
    # Validar permisos
    if request.user.id != user_id:
        messages.error(request, "No tienes permiso para ver este historial.")
        return redirect('home')

    # Obtener estudiante
    estudiante = get_object_or_404(Usuario, id=user_id)

    # Obtener tutorías completadas
    tutorias = Tutoria.objects.filter(
        estudiante=estudiante
    ).select_related('tutor').prefetch_related('evaluaciones__realizaciones').order_by('-hora_inicio')

    # Recorrer tutorías y evaluaciones para marcar si se puede realizar
    for tutoria in tutorias:
        for evaluacion in tutoria.evaluaciones.all():
            # Obtener la realización del estudiante si existe
            realizacion = evaluacion.realizaciones.filter(estudiante=estudiante).first()
            if realizacion:
                evaluacion.puede_realizar = False
                evaluacion.realizacion = realizacion  # Guardamos para mostrar resultados
            else:
                evaluacion.puede_realizar = True
                evaluacion.realizacion = None

    # Obtener archivos asociados (opcional)
    archivos_asociados = Archivo.objects.filter(tutoria__in=tutorias)

    contexto = {
        'tutorias': tutorias,
        'archivos': archivos_asociados,
    }

    return render(request, 'home/historialtutorias.html', contexto)

@login_required
def dejar_de_ser_tutor(request):
    if request.method != "POST":
        return redirect("perfilusuario")

    usuario = request.user

    try:
        with transaction.atomic():

            # Quitar rol de tutor si existe
            try:
                rol_tutor = usuario.roles.get(nombre="Tutor")
                usuario.roles.remove(rol_tutor)
            except usuario.roles.model.DoesNotExist:
                pass

            # Marcar el modelo Tutor como inactivo si existe
            try:
                tutor = Tutor.objects.select_for_update().get(usuario=usuario)
                tutor.estado = Tutor.EstadoTutor.INACTIVO
                tutor.save()

                # Desactivar áreas
                for ta in tutor.areastutor.filter(activo=True):
                    ta.desactivar()
            except Tutor.DoesNotExist:
                pass

        # ÉXITO → forzar logout
        logout(request)
        messages.success(request, "Has dejado de ser tutor. Tu sesión ha sido cerrada.")
        return redirect("login")  # O la ruta que uses

    except Exception as e:
        messages.error(request, "No se pudo completar la operación. Intente nuevamente.")
        logger.error(
            f"Error en dejar_de_ser_tutor para usuario {usuario.id}: {e}",
            exc_info=True
        )
        return redirect("perfilusuario")
    
@login_required
def estado_cancelado(request, solicitud_id):
    """
    Devuelve si la solicitud de tutoría ha sido cancelada por el tutor.
    """
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    # Solo el estudiante receptor puede consultar si fue cancelada
    if solicitud.usuarioreceive != request.user:
        return JsonResponse({"error": "No tienes permisos para ver esta solicitud."}, status=403)

    data = {
        "cancelada": solicitud.estado == "Cancelada"
    }

    return JsonResponse(data)