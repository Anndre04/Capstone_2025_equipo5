from django.urls import path
from . import views

# notificaciones/urls.py
urlpatterns = [
    path('lista/', views.lista_notificaciones, name='lista_notificaciones'),
    path('<uuid:notificacion_id>/marcar-leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('no-leidas/', views.notificacionesno_leidas, name='contar_notificaciones_no_leidas'),
]
