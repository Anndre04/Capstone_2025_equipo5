from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('perfilusuario/<int:user_id>', views.perfilusuario, name="perfilusuario"),
    path('solicitudesusuario/<int:user_id>', views.solicitudesusuario, name="solicitudesusuario"),
    path('cancelar/<int:solicitud_id>/', views.cancelarsolicitud, name='cancelarsolicitud'),
]
