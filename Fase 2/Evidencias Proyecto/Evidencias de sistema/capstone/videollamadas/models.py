import uuid
from django.db import models
from tutoria.models import Tutoria

# Create your models here.

class Videollamada(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tutoria = models.ForeignKey(Tutoria, on_delete=models.PROTECT, related_name='grabaciones')
    video_url = models.URLField(max_length=500)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tutoria.titulo} - {self.fecha_subida.strftime('%Y-%m-%d %H:%M')}"