from django.urls import path
from . import views

app_name = 'tutoria'

urlpatterns = [
    path('mistutoriasprof/<int:user_id>/', views.mistutoriasprof, name='mistutoriasprof'),
    path('anunciotutor/<int:anuncio_id>', views.anunciotutor, name='anunciotutor'),
    path('solicitudesprof/<int:user_id>', views.solicitudesprof, name='solicitudesprof'),    
    path('solicitud/<int:solicitud_id>/aceptar/', views.aceptar_solicitud, name='aceptar_solicitud'),
    path('solicitud/<int:solicitud_id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('gestortutorias', views.gestortutorias, name='gestortutorias'),
    path('perfil', views.perfil, name='perfil'),
    path('perfilusuario', views.perfilusuario, name='perfilusuario'),
    
    

]
