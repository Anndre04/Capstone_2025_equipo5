from django.db import models
from autenticacion.models import AreaInteres
from django.conf import settings

# Create your models here.

class TipoSolicitud(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre
    
class Solicitud(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes", null=True
    )
    tipo = models.ForeignKey(TipoSolicitud, on_delete=models.PROTECT)
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[("Pendiente", "Pendiente"), ("Aceptada", "Aceptada"), ("Rechazada", "Rechazada")],
        default="Pendiente"
    )

    anuncio = models.ForeignKey("Anuncio", on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"Solicitud {self.tipo.nombre} de {self.estudiante.email}"
    

class Archivo(models.Model):
     contenido = models.CharField(max_length=200)

class Tutor(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    areas_conocimiento = models.ManyToManyField(
        to=AreaInteres,
        through='TutorArea',
        related_name='tutores'
    )
    archivo = models.ManyToManyField(to=Archivo)
    estado = models.CharField(max_length=30)

    def __str__(self):
        return str(self.usuario)
    
class TutorArea(models.Model):
    tutor = models.ForeignKey(to=Tutor, on_delete=models.PROTECT)
    area = models.ForeignKey(to=AreaInteres, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_desactivado = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('tutor', 'area')

class Disponibilidad_tutor(models.Model):
    tutor = models.ForeignKey(to=Tutor, on_delete=models.PROTECT, null=True)

    DIAS_SEMANA = [
        ("Lunes", "Lunes"),
        ("Martes", "Martes"),
        ("Miércoles", "Miércoles"),
        ("Jueves", "Jueves"),
        ("Viernes", "Viernes"),
        ("Sábado", "Sábado"),
        ("Domingo", "Domingo"),
    ]

    dia = models.CharField(max_length=15, choices=DIAS_SEMANA)
    mañana = models.BooleanField()
    tarde = models.BooleanField()
    noche = models.BooleanField()
    

class Anuncio(models.Model):
    tutor = models.ForeignKey(to=Tutor, on_delete=models.PROTECT)
    area = models.ForeignKey(to=AreaInteres, on_delete=models.PROTECT, null=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        # Validar que el tutor no tenga otro anuncio con la misma área activo
        if Anuncio.objects.filter(tutor=self.tutor, area=self.area, activo=True).exclude(id=self.id).exists():
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Ya existe un anuncio activo para el área {self.area}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.titulo} - {self.area} - {self.tutor}"