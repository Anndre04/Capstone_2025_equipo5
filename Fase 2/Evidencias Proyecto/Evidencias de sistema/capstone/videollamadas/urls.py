from django.urls import path
from . import views

urlpatterns = [
    path("index/<uuid:tutoria_id>/", views.index, name="index"),
    path("grabacion/iniciar/<uuid:tutoria_id>/", views.iniciar_grabacion, name="iniciar_grabacion"),
    path('grabacion/detener/<uuid:tutoria_id>/', views.detener_grabacion, name='detener_grabacion'),

]
