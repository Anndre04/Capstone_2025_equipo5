from django.urls import path
from . import views

urlpatterns = [
    path('crearevaluacion/<uuid:tutoria_id>', views.crear_evaluacion, name='crearevaluacion'),
    path('responder/<uuid:evaluacion_id>/', views.responder_evaluacion, name='responder_evaluacion'),
]