from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from autenticacion.models import Usuario
from django.contrib.auth.decorators import login_required
from .models import Notificacion
from tutoria.models import Solicitud


# Create your views here.

@login_required
def notificacionesno_leidas(request):
    count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    return JsonResponse({'count': count})


@login_required
def lista_notificaciones(request):
    try:
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
    except Exception as e:
        # Logea el error en la consola o en un logger
        print(f"Error obteniendo notificaciones: {e}")
        # Devuelve JSON con error
        return JsonResponse({'success': False, 'error': 'Error obteniendo notificaciones'}, status=500)
    

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