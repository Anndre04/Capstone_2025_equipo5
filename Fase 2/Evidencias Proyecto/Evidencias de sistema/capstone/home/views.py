from datetime import datetime, timedelta
from django.conf import settings
from django.urls import reverse
import logging
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from autenticacion.tasks import BASE_URL
from tutoria.models import Anuncio, Archivo, TipoSolicitud, Tutor, TutorArea, Tutoria
from autenticacion.models import AreaInteres, Usuario, UsuarioArea
from tutoria.models import Anuncio, Solicitud
from django.db.models import Avg, Case, When, Value, IntegerField

from tutoria.views import generar_url_firmada_gcs


logger = logging.getLogger(__name__)

def home(request):

    try:
        anuncios = Anuncio.objects.filter(estado='Activo')
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
    # 1. Obtenemos el objeto Usuario autenticado (sin consulta extra)
    usuario = request.user

    contexto = {
            'usuario': usuario
        }
    
    try:
        tutor = Tutor.objects.prefetch_related('areastutor', 'certificados').get(usuario=usuario)

        logger.warning(vars(tutor))

        contexto['tutor'] = tutor
        contexto['areastutor'] = tutor.areastutor.filter(activo=True)
        contexto['es_tutor'] = True

        archivos = tutor.certificados.all()
        archivos_con_url = []

        for archivo in archivos:
            archivos_con_url.append({
                "nombre": archivo.nombre,
                "estado": archivo.estado,
                "url_ver": generar_url_firmada_gcs(archivo.url, descargar=False),
                "url_descargar": generar_url_firmada_gcs(archivo.url, descargar=True)
            })

        contexto["archivos"] = archivos_con_url
        
    except Tutor.DoesNotExist:
        contexto['es_tutor'] = False
        
    except Exception as e:
        messages.error(request, "Hubo un error cargando su perfil. Inténtelo más tarde.")
        logger.error(f"Error cargando perfil del usuario {usuario.id}", exc_info=True)
        return redirect("home")

    return render(request, 'home/perfilusuario.html', contexto)

# perfil/views.py
@login_required
def editar_perfil(request):
    usuario = request.user

    # Obtener instancias relacionadas (si existen)
    tutor = getattr(usuario, 'tutor', None)
    usuario_areas = UsuarioArea.objects.filter(usuario=usuario, activo=True)
    tutor_areas = TutorArea.objects.filter(tutor=tutor, activo=True) if tutor else []
    archivos = Archivo.objects.filter(tutor=tutor) if tutor else []

    if request.method == 'POST':
        tipo = request.POST.get('tipo')  # Identificar qué sección se envía

        # --- DATOS PERSONALES (Usuario) ---
        if tipo == 'usuario':
            usuario.nombre = request.POST.get('nombre')
            usuario.p_apellido = request.POST.get('p_apellido')
            usuario.s_apellido = request.POST.get('s_apellido')
            usuario.genero = request.POST.get('genero')
            usuario.fecha_nac = request.POST.get('fecha_nac')
            usuario.ocupacion_id = request.POST.get('ocupacion')
            usuario.n_educacion_id = request.POST.get('n_educacion')
            usuario.institucion_id = request.POST.get('institucion')
            usuario.save()

            return JsonResponse({'ok': True, 'msg': 'Datos personales actualizados'})

        # --- PERFIL TUTOR ---
        elif tipo == 'tutor':
            if tutor:
                tutor.sobremi = request.POST.get('sobremi')
                tutor.save()
                return JsonResponse({'ok': True, 'msg': 'Perfil de tutor actualizado'})
            else:
                return JsonResponse({'ok': False, 'msg': 'No tienes perfil de tutor'})

        # --- ÁREAS DE INTERÉS (UsuarioArea) ---
        elif tipo == 'usuario_area':
            areas_ids = request.POST.getlist('areas[]')
            UsuarioArea.objects.filter(usuario=usuario).update(activo=False)
            for area_id in areas_ids:
                UsuarioArea.objects.update_or_create(
                    usuario=usuario,
                    area_id=area_id,
                    defaults={'activo': True}
                )
            return JsonResponse({'ok': True, 'msg': 'Áreas de interés actualizadas'})

        # --- ÁREAS DE CONOCIMIENTO (TutorArea) ---
        elif tipo == 'tutor_area' and tutor:
            areas_ids = request.POST.getlist('areas[]')
            TutorArea.objects.filter(tutor=tutor).update(activo=False)
            for area_id in areas_ids:
                TutorArea.objects.update_or_create(
                    tutor=tutor,
                    area_id=area_id,
                    defaults={'activo': True}
                )
            return JsonResponse({'ok': True, 'msg': 'Áreas de conocimiento actualizadas'})

        # --- ARCHIVOS (Archivo) ---
        elif tipo == 'archivo' and tutor:
            archivo = request.FILES.get('archivo')
            nombre = request.POST.get('nombre')

            # Aquí subirías el archivo al bucket o filesystem
            # y guardarías la URL resultante en `Archivo.url`
            Archivo.objects.create(
                tutor=tutor,
                nombre=nombre,
                url='ruta/o/url/generada',
                estado='Pendiente'
            )
            return JsonResponse({'ok': True, 'msg': 'Archivo subido con éxito'})

    # GET → Renderizar la página
    context = {
        'usuario': usuario,
        'tutor': tutor,
        'usuario_areas': usuario_areas,
        'tutor_areas': tutor_areas,
        'archivos': archivos,
    }
    return render(request, 'perfil/editar_perfil.html', context)


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
        dt_fin = dt_inicio + timedelta(minutes=30)

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
    ).select_related('tutor').prefetch_related('evaluaciones__realizaciones')

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

