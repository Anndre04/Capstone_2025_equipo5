from django.urls import path
from . import views

app_name = 'tutoria'

urlpatterns = [
    path('anunciotutor/', views.anunciotutor, name='anunciotutor'),
    path('mistutoriasprof/', views.mistutoriasprof, name='mistutoriasprof'),
    path('solicitudesprof/', views.solicitudesprof, name='solicitudesprof'),    
    path('gestortutorias/', views.gestortutorias, name='gestortutorias'),
]
