from django.contrib import admin
from .models import Pais, AreaInteres, Comuna, Region, Institucion, Ocupacion, Nivel_educacional, Rol, Usuario, UsuarioArea

# Register your models here.

admin.site.register(Pais)
admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(AreaInteres)
admin.site.register(Ocupacion)
admin.site.register(Nivel_educacional)
admin.site.register(Institucion)
admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(UsuarioArea)