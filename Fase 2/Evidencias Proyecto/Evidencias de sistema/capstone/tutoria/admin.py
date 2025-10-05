from django.contrib import admin
from .models import Tutor, TutorArea, Archivo, TipoSolicitud, Anuncio, Solicitud, Disponibilidad

# Register your models here.

admin.site.register(Tutor)
admin.site.register(TutorArea)
admin.site.register(Archivo)
admin.site.register(TipoSolicitud)
admin.site.register(Anuncio)
admin.site.register(Solicitud)
admin.site.register(Disponibilidad)