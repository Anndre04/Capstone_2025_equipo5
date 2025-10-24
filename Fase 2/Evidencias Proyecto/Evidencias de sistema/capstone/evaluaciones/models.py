import uuid
from django.db import models
from tutoria.models import Tutoria
from autenticacion.models import Usuario

# Create your models here.

class TipoPregunta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Pregunta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contenido = models.CharField(max_length=500)
    puntos = models.IntegerField()
    tipo = models.ForeignKey(TipoPregunta, on_delete=models.PROTECT, related_name='preguntas')

    def __str__(self):
        return self.contenido


class Respuesta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT, related_name='respuestas')
    contenido = models.CharField(max_length=250)
    correcto = models.BooleanField(default=False)

    def __str__(self):
        return self.contenido
    

class Evaluacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=100)
    fecha_creacion = models.DateField(auto_now_add=True)
    preguntas = models.ManyToManyField(Pregunta, through='EvaluacionPregunta')
    tutoria = models.ForeignKey(Tutoria, on_delete=models.PROTECT)
    #puntaje_total
    #puntaje_obtenido

    def __str__(self):
        return f"Evaluación {self.id} - {self.fecha_creacion}"
    

class EvaluacionPregunta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.PROTECT, related_name='evaluacion_preguntas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT)
    estudiante = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    respuesta_seleccionada = models.ForeignKey(
        Respuesta,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    puntaje_obtenido = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estudiante} - {self.pregunta}"