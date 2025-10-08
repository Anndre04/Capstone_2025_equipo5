from django.shortcuts import render
from django.http import JsonResponse
from tutoria.models import Anuncio, Tutor
from django.contrib.auth.decorators import login_required
from autenticacion.models import AreaInteres
from .models import Notificacion

# Create your views here.

def home(request):
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

@login_required
def notificacionesno_leidas(request):
    count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    return JsonResponse({'count': count})


@login_required
def lista_notificaciones(request):
    """Obtiene las últimas notificaciones para el dropdown"""
    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    ).select_related('tipo').order_by('-fecha_creacion')[:10]
    
    data = {
        'notificaciones': [
            {
                'id': n.id,
                'tipo': n.tipo.codigo,
                'titulo': n.titulo,
                'mensaje': n.mensaje,
                'icono': n.tipo.icono,
                'color': n.tipo.color,
                'fecha_creacion': n.fecha_creacion.isoformat(),
                'leida': n.leida,
                'datos_extra': n.datos_extra
            } for n in notificaciones
        ],
        'total_no_leidas': Notificacion.objects.filter(
            usuario=request.user, leida=False
        ).count()
    }
    
    return JsonResponse(data)

@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación como leída"""
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
        notificacion.leida = True
        notificacion.save()
        return JsonResponse({'success': True})
    except Notificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notificación no encontrada'})

@login_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones como leídas"""
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return JsonResponse({'success': True})
