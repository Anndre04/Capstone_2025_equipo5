from django.urls import path
from .views import chat, mensajes_view

urlpatterns = [
    path('', chat, name='chat'),
    path('mensajes/<int:chat_id>/', mensajes_view, name='obtener_mensajes'),
]