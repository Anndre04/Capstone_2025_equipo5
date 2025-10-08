from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('registro/', views.registro_view, name='registro'),
    path("activar/<str:token>/", views.verificar_email, name="verificar_email"),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('seleccionar-rol/', views.seleccionar_rol, name='seleccionar_rol'),
]