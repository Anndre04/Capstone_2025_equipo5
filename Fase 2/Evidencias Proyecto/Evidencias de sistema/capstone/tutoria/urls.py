from django.urls import path
from . import views

app_name = 'tutoria'

urlpatterns = [
    path('publicartutoria/<uuid:user_id>/', views.publicartutoria, name='publicartutoria'),
    path('misanunciosprof/<uuid:user_id>/', views.misanunciosprof, name='misanunciosprof'),
    path('anunciotutor/<uuid:anuncio_id>', views.anunciotutor, name='anunciotutor'),
    path('solicitudesprof/<uuid:user_id>', views.solicitudesprof, name='solicitudesprof'),
    path('enviar-solicitud/<uuid:anuncio_id>/', views.enviar_solicitud, name='enviarsolicitud'),
    path('solicitud/<uuid:solicitud_id>/aceptar/', views.aceptar_solicitud, name='aceptar_solicitud'),
    path('solicitud/<uuid:solicitud_id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('gestortutorias', views.gestortutorias, name='gestortutorias'),
    path('estado-anuncio/<uuid:anuncio_id>', views.estadoanuncio, name='estadoanuncio'),
    path('editaranuncio/<uuid:anuncio_id>', views.editaranuncio, name="editaranuncio"),
    path('eliminaranuncio/<uuid:anuncio_id>/', views.eliminar_anuncio, name='eliminar_anuncio'),
    path('perfiltutor/<uuid:tutor_id>', views.perfiltutor, name='perfiltutor'),
    path('registrotutor', views.registrotutor, name='registrotutor'),
    path('gestortutorias/<uuid:user_id>', views.gestortutorias, name='gestortutorias'),
    path("obtener-alumnos/<uuid:anuncio_id>/", views.obtener_alumnos_anuncio, name="obtener_alumnos_por_anuncio"),
    path('crear-solicitud-tutoria/', views.crear_solicitud_tutoria, name='crear_solicitud_tutoria'),
    path('estado-solicitud/<uuid:solicitud_id>/', views.estado_solicitud_tutoria, name='estado_solicitud_tutoria'),
    path('tutoria/<uuid:tutoria_id>', views.tutoria, name='tutoria'),
    path('estado-tutoria/<uuid:tutoria_id>/', views.estado_tutoria, name='estadotutoria'),
    path('tutoria-completada/<uuid:tutoria_id>/', views.tutoria_completada, name='estadotutoria'),
    path('reseña/<uuid:tutoria_id>/', views.crear_reseña, name='crear_reseña'),
]
