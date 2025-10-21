from django.contrib import admin
from .models import Evaluacion, Pregunta, TipoPregunta, Respuesta, EvaluacionPregunta

# Register your models here.

admin.site.register(Evaluacion)
admin.site.register(Pregunta)
admin.site.register(TipoPregunta)
admin.site.register(Respuesta)
admin.site.register(EvaluacionPregunta)
