from django.db import models
from django.forms import ValidationError
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

    def clean(self):
        """
        Llama a las validaciones específicas según el tipo de solicitud.
        """
        self.validar_solicitudes_normales()
        self.validar_tutorias_activas()

    def validar_solicitudes_normales(self):
        """
        Valida que no haya otra solicitud activa del mismo tipo entre los mismos usuarios
        (excepto si es 'Tutoria').
        """
        if self.tipo.nombre.lower() == "tutoria":
            return  # no aplica para tutorías

        qs = Solicitud.objects.filter(
            usuarioenvia=self.usuarioenvia,
            usuarioreceive=self.usuarioreceive,
            tipo=self.tipo,
            estado__in=["Pendiente", "Aceptada"]
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                f"Ya existe una solicitud activa de tipo '{self.tipo.nombre}' entre estos usuarios."
            )

    def validar_tutorias_activas(self):
        """
        Valida que no exista una tutoría en curso entre los mismos usuarios.
        """
        if self.tipo.nombre.lower() != "tutoria":
            return  # solo aplica para tutorías

        from .models import Tutoria  # evitar import circular
        tutor = self.usuarioenvia.tutor
        estudiante = self.usuarioreceive

        tutoria_activa = Tutoria.objects.filter(
            tutor=tutor,
            estudiante=estudiante,
            estado__in=["Pendiente", "En curso"]
        )
        if self.pk:
            tutoria_activa = tutoria_activa.exclude(solicitud__pk=self.pk)

        if tutoria_activa.exists():
            raise ValidationError(
                "Ya existe una tutoría activa entre estos usuarios."
            )

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
    contenido = models.BinaryField()
    tutor = models.ForeignKey(Tutor, on_delete=models.PROTECT, related_name="archivos", null=True)
    estado = models.CharField(max_length=20, choices=estado, null=True)

    def __str__(self):
        return self.nombre or "Archivo sin nombre"
    
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
    estado = models.CharField(max_length=20, choices=estado, null=True)

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
    solicitud = models.ForeignKey(Solicitud, on_delete=models.PROTECT, related_name="tutoria_creada", null=True)
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
            ("Completada", "Completada"),
            ("Cancelada", "Cancelada"),
            ("En curso", "En curso"),
        ],
        default="Pendiente"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tutoria de {self.estudiante} con {self.tutor} ({self.fecha})"