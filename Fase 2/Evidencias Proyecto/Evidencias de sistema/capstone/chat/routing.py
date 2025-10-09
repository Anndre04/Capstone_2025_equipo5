from django.urls import path, re_path
from .consumer import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<chat_id>/', ChatConsumer.as_asgi()),
]