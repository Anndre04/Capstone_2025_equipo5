from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Pais, Region, Comuna, Ocupacion, AreaInteres, Rol, Nivel_educacional, Institucion, UsuarioArea


admin.site.register(UsuarioArea)
admin.site.register(Usuario)
admin.site.register(Pais)
admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Ocupacion)
admin.site.register(AreaInteres)
admin.site.register(Rol)
admin.site.register(Nivel_educacional)
admin.site.register(Institucion)