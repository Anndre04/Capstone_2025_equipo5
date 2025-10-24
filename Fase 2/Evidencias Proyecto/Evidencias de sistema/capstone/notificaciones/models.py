import uuid
from django.db import models
from autenticacion.models import Usuario

# Create your models here.

class TipoNotificacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True, null=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, default='bi-bell', null=True)
    color = models.CharField(max_length=20, default='primary', null=True)
    activo = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre
    
class Notificacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    tipo = models.ForeignKey(TipoNotificacion, on_delete=models.PROTECT)
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    datos_extra = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.tipo.nombre} - {self.usuario}"