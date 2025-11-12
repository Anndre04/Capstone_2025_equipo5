from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('registro/', views.registro_view, name='registro'),
    path("activar/<str:token>/", views.verificar_email, name="verificar_email"),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('seleccionar-rol/', views.seleccionar_rol, name='seleccionar_rol'),
    path('obtener_comunas/<uuid:region_id>/', views.obtener_comunas, name='obtener_comunas'),
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name="autenticacion/password_reset/password_reset_done.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="autenticacion/password_reset/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name="autenticacion/password_reset/password_reset_complete.html"), name='password_reset_complete'),
]