from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('perfilusuario/', views.perfilusuario, name="perfilusuario"),
    path('solicitudesusuario/<uuid:user_id>', views.solicitudesusuario, name="solicitudesusuario"),
    path('cancelar/<uuid:solicitud_id>/', views.cancelarsolicitud, name='cancelarsolicitud'),
    path('rechazar_tutoria/<uuid:solicitud_id>/', views.rechazar_solicitud_tutoria, name="rechazar_tutoria"),
    path('aceptar_tutoria/<uuid:solicitud_id>/', views.aceptar_solicitud_tutoria, name="aceptar_tutoria"),
    path('historial_tutoria/<uuid:user_id>/', views.historial_tutoria, name="historial_tutoria")
]
