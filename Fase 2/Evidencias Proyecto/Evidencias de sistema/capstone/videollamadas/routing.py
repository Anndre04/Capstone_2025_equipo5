from django.urls import re_path
from .consumers import TutoriaConsumer

websocket_urlpatterns = [
    re_path(r'ws/tutoria/(?P<tutoria_id>[0-9a-f-]+)/$', TutoriaConsumer.as_asgi()),
]
