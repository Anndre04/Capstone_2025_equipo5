from django.contrib import admin
from .models import Evaluacion, Pregunta, TipoPregunta, Respuesta, EvaluacionPregunta, TipoEvaluacion, RealizacionRespuesta, Realizacion

# Register your models here.

admin.site.register(Evaluacion)
admin.site.register(Pregunta)
admin.site.register(TipoPregunta)
admin.site.register(Respuesta)
admin.site.register(EvaluacionPregunta)
admin.site.register(TipoEvaluacion)
admin.site.register(Realizacion)
admin.site.register(RealizacionRespuesta)
