from django.urls import path
from . import views

# notificaciones/urls.py
urlpatterns = [
    path("index/<uuid:tutoria_id>/", views.index, name="index"),
]
