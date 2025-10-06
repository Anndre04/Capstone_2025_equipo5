from django.urls import path
from . import views

app_name = 'tutoria'

urlpatterns = [
    path('mistutoriasprof/', views.mistutoriasprof, name='mistutoriasprof'),
    path('anunciotutor/', views.anunciotutor, name='anunciotutor'),
    path('solicitudesprof/', views.solicitudesprof, name='solicitudesprof'),    
]
