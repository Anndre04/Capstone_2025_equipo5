from django.urls import path
from . import views

urlpatterns = [
    path('crearevaluacion/<int:tutoria_id>', views.crear_evaluacion, name='crearevaluacion'),
    path('responder/<int:evaluacion_id>/', views.responder_evaluacion, name='responder_evaluacion'),
]