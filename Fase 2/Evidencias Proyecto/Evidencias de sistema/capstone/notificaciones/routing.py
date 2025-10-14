from django.urls import re_path
from .consumer import NotificacionConsumer

websocket_urlpatterns = [
    re_path('ws/notificaciones/', NotificacionConsumer.as_asgi()),
]