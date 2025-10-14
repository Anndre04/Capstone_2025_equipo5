import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tutoria.models import Anuncio
from autenticacion.models import AreaInteres, Usuario
from tutoria.models import Anuncio, Solicitud

logger = logging.getLogger(__name__) 

def home(request):
    try:
        anuncios = Anuncio.objects.filter(estado='Activo')
        areainteres = AreaInteres.objects.all()

        # Obtener filtros del GET
        nombre = request.GET.get('nombre', '')
        precio_max = request.GET.get('precio_max', '')
        asignatura_id = request.GET.get('asignatura', '')

        # Filtrar por nombre del tutor
        if nombre:
            anuncios = anuncios.filter(tutor__usuario__nombre__icontains=nombre)

        # Filtrar por precio máximo
        if precio_max:
            anuncios = anuncios.filter(precio__lte=precio_max)

        # Filtrar por asignatura / área de interés
        if asignatura_id:
            anuncios = anuncios.filter(area__id=asignatura_id)

        contexto = {
            "anuncios": anuncios,
            "areas": areainteres,
            "filtros": {
                "nombre": nombre,
                "precio_max": precio_max,
                "asignatura": asignatura_id,
            }
        }

        return render(request, 'home/home.html', contexto)
    
    except Exception:
        messages.error(request, "Hubo un error cargando la página principal. Inténtelo más tarde.")
        logger.error("Error en home view", exc_info=True)
        return redirect("home")

@login_required
def perfilusuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    
    try:
    
        contexto = {
            'usuario': usuario
        }

        return render(request, 'home/perfilusuario.html', contexto)
    except Exception:
        messages.error(request, "Hubo un error accediendo a su perfil")
        logger.error("Error obteniendo perfil del usuario", exc_info=True)
        return redirect("home")


@login_required
def solicitudesusuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    
    try:
        solicitudes = Solicitud.objects.filter(usuarioenvia=usuario, estado__in=["Aceptada", "Pendiente", "Rechazada"])
        
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
