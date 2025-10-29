from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('perfilusuario/<int:user_id>', views.perfilusuario, name="perfilusuario"),
    path('solicitudesusuario/<int:user_id>', views.solicitudesusuario, name="solicitudesusuario"),
    path('cancelar/<int:solicitud_id>/', views.cancelarsolicitud, name='cancelarsolicitud'),
    path('rechazar_tutoria/<int:solicitud_id>/', views.rechazar_solicitud_tutoria, name="rechazar_tutoria"),
    path('aceptar_tutoria/<int:solicitud_id>/', views.aceptar_solicitud_tutoria, name="aceptar_tutoria"),
    path('tutoriasagregadas/<int:user_id>', views.tutoriasagregadas, name='tutoriasagregadas'),
]
