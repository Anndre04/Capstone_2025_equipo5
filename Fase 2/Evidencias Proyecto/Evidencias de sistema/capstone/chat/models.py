from django.db import models
from autenticacion.models import Usuario 

# Create your models here.

class Chat(models.Model):
    nombre = models.CharField(max_length=50)
    users = models.ManyToManyField(Usuario, related_name="chats")
    fecha_creacion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=30)

    def save(self, *args, **kwargs):
        if self.pk:
            if self.users.count() > 2:
                raise ValueError("Un chat 1:1 no puede tener más de 2 usuarios")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    
class Mensaje(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.PROTECT, verbose_name="Usuario")
    chat = models.ForeignKey(Chat, on_delete=models.PROTECT, verbose_name="Chat")
    mensaje = models.TextField(verbose_name="Mensaje")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Enviado")
    enviado = models.BooleanField()
    leido = models.BooleanField()

    def __str__(self):
        return self.mensaje