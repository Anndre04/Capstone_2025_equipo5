from django.db import models
from autenticacion.models import AreaInteres, Usuario
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

# Create your models here.

class TipoSolicitud(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre
    
class Solicitud(models.Model):
    usuarioenvia = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="solicitudes", null=True
    )
    usuarioreceive = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="solicitudes_recibidas", null=True
    )
    tipo = models.ForeignKey(TipoSolicitud, on_delete=models.PROTECT)
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[("Pendiente", "Pendiente"), ("Aceptada", "Aceptada"), ("Rechazada", "Rechazada"), ("Cancelada", "Cancelada")],
        default="Pendiente"
    )

    anuncio = models.ForeignKey("Anuncio", on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['usuarioenvia', 'usuarioreceive'],
                condition=models.Q(estado__in=['Pendiente', 'Aceptada']),
                name='unique_solicitud_activa'
            )
        ]

    def __str__(self):
        return f"Solicitud {self.tipo.nombre} de {self.usuarioenvia.email}"
    

class Tutor(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    areas_conocimiento = models.ManyToManyField(
        to=AreaInteres,
        through='TutorArea',
        related_name='tutores'
    )

    estado = models.CharField(max_length=30)

    def __str__(self):
        return str(self.usuario)
    

    
class Archivo(models.Model):

    estado = [
        ("Revisado", "Revisado"),
        ("Pendiente", "Pendiente"),
        ("Rechazado", "Rechazado"),
    ]

    nombre = models.CharField(max_length=80, null=True)
    contenido = models.CharField(max_length=200)
    tutor = models.ForeignKey(Tutor, on_delete=models.PROTECT, related_name="archivos", null=True)
    estado = models.CharField(max_length=20, choices=estado, null=True)

    def __str__(self):
        return self.nombre
    
class TutorArea(models.Model):
    tutor = models.ForeignKey(to=Tutor, on_delete=models.PROTECT, null=True)
    area = models.ForeignKey(to=AreaInteres, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_desactivado = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('tutor', 'area') 

    def __str__(self):
        return self.area.nombre

class Anuncio(models.Model):

    estado = [
        ("Activo", "Activo"),
        ("Deshabilitado", "Deshabilitado"),
        ("Eliminado", "Eliminado"),
    ]

    tutor = models.ForeignKey(to=Tutor, on_delete=models.PROTECT, related_name="anuncios")
    area = models.ForeignKey(to=TutorArea, on_delete=models.PROTECT, null=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.IntegerField(validators=[
            MinValueValidator(5000),
            MaxValueValidator(1000000)
        ])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=estado)

    def clean(self):
        # Validar que el tutor no tenga otro anuncio con la misma área activo
        if Anuncio.objects.filter(tutor=self.tutor, area=self.area, estado=['Activo', 'Deshabilitado']).exclude(id=self.id).exists():
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Ya existe un anuncio creado para el área de: {self.area}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.titulo} - {self.area} - {self.tutor}"
    
class Disponibilidad(models.Model):
    anuncio = models.ForeignKey(to=Anuncio, on_delete=models.PROTECT, null=True)

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
    mañana = models.BooleanField(default=False)
    tarde = models.BooleanField(default=False)
    noche = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.anuncio.id} - {self.dia} - {self.mañana}"
    
class Tutoria(models.Model):
    solicitud = models.OneToOneField(
        to=Solicitud,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tutoria"
    )
    anuncio = models.ForeignKey(
        to=Anuncio,
        on_delete=models.PROTECT,
        related_name="tutorias"
    )
    tutor = models.ForeignKey(
        to=Tutor,
        on_delete=models.PROTECT,
        related_name="tutorias"
    )
    estudiante = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tutorias_recibidas"
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(
        max_length=20,
        choices=[
            ("Pendiente", "Pendiente"),
            ("Confirmada", "Confirmada"),
            ("Completada", "Completada"),
            ("Cancelada", "Cancelada"),
        ],
        default="Pendiente"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tutoria de {self.estudiante} con {self.tutor} ({self.fecha})"