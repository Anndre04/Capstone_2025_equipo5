from django.contrib import admin
from .models import Notificacion, TipoNotificacion

# Register your models here.

admin.site.register(Notificacion)
admin.site.register(TipoNotificacion)