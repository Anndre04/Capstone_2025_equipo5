from django.urls import re_path
from .consumers import TutoriaConsumer

websocket_urlpatterns = [
    re_path(r'ws/tutoria/(?P<tutoria_id>\d+)/$', TutoriaConsumer.as_asgi()),
]