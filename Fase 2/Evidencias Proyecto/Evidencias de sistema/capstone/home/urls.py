from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('notificaciones/lista/', views.lista_notificaciones, name='lista_notificaciones'),
    path('notificaciones/<int:notificacion_id>/marcar-leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('notificaciones/no-leidas/', views.notificacionesno_leidas, name='contar_notificaciones_no_leidas'),
    path('perfilusuario/<int:user_id>', views.perfilusuario, name="perfilusuario"),
    path('solicitudesusuario/<int:user_id>', views.solicitudesusuario, name="solicitudesusuario"),
    path('cancelar/<int:solicitud_id>/', views.cancelarsolicitud, name='cancelarsolicitud'),
]
