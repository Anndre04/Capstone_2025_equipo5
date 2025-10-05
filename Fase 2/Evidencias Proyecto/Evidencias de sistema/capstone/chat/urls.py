from django.urls import path
from .views import chat, mensajes_view, crear_chat, marcar_leidos

urlpatterns = [
    path('', chat, name='chat'),
    path('mensajes/<int:chat_id>/', mensajes_view, name='obtener_mensajes'),
    path('chat/crear/<int:user_id>/', crear_chat, name='crear_chat'),
    path('marcar_leidos/<int:chat_id>/', marcar_leidos, name='marcar_leidos'),
]