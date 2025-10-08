from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from autenticacion import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('auth/', include('autenticacion.urls')),
    path('tutoria/', include('tutoria.urls')),
    path('chat/', include('chat.urls')),
    path('activar/<str:token>/', auth_views.verificar_email, name='activar_cuenta'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, documento_root = settings.STATIC_ROOT)