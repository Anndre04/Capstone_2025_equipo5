from django.urls import path
from .views import chat, mensajes_view, crear_chat, marcar_leidos

urlpatterns = [
    path('', chat, name='chat'),
    path('mensajes/<uuid:chat_id>/', mensajes_view, name='obtener_mensajes'),
    path('crearchat/<uuid:user_id>/', crear_chat, name='crearchat'),
    path('marcar_leidos/<uuid:chat_id>/', marcar_leidos, name='marcar_leidos'),
]