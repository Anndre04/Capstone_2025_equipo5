import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from datetime import timedelta
from django.conf import settings
from google.cloud import storage
import logging

# Create your models here.
logger = logging.getLogger(__name__)

try:
    GCP_CLIENT = storage.Client.from_service_account_json(
        settings.GOOGLE_APPLICATION_CREDENTIALS
    )
    GCP_BUCKET = GCP_CLIENT.get_bucket(settings.GOOGLE_CLOUD_BUCKET)
except Exception as e:
    logger.error("Error al inicializar el cliente de GCP en models.py", exc_info=True)
    GCP_BUCKET = None


def generar_url_firmada(nombre_objeto, expiracion=3600):
    """Genera una URL firmada de Cloud Storage para lectura (GET)."""
    
    if GCP_BUCKET is None:
        raise ConnectionError("GCP Bucket no inicializado. Revisar configuración.")
    
    blob = GCP_BUCKET.blob(nombre_objeto)
    
    # Genera la URL temporal (v4)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=expiracion), 
        method="GET"
    )
    return url

class Pais(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=80)

    def __str__(self):
        return self.nombre

class Region(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    numero = models.CharField(max_length=5, unique=True)

    def __str__(self):
        return self.nombre

class Comuna(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="comunas")

    def __str__(self):
        return f"{self.nombre}"
    
class Nivel_educacional(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nombre}"

class AreaInteres(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Ocupacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre}"
    
class TipoInstitucion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.nombre}"

class Institucion(models.Model):
    ESTADOS = [
        ('VIGENTE', 'Vigente'),
        ('NO_VIGENTE', 'No vigente'),
        ('EN_CIERRE', 'En proceso de cierre'),
        ('REVOCADA', 'Reconocimiento revocado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200)
    tipo_institucion = models.ForeignKey(TipoInstitucion, on_delete=models.PROTECT, null=True, related_name="tipoinstitucion")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='VIGENTE')
    neducacional = models.ForeignKey(Nivel_educacional, on_delete=models.PROTECT, null=True, related_name="niveleducacional")
    
    def __str__(self):
        return self.nombre
    
class Rol(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=40)

    def __str__(self):
        return self.nombre

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)
    
class Usuario(AbstractBaseUser, PermissionsMixin):

    GENERO_CHOICES = [
        ("H", "Hombre"),
        ("M", "Mujer"),
        ("O", "Otro"),
        ("N", "Prefiero no decirlo"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    p_apellido = models.CharField(max_length=50, blank=True, null=True)
    s_apellido = models.CharField(max_length=50, blank=True, null=True)
    run = models.CharField(max_length=10, blank=True, null=True)
    roles = models.ManyToManyField(to=Rol)
    pais = models.ForeignKey(to=Pais, on_delete=models.PROTECT, null=True, blank=True)
    region = models.ForeignKey(to=Region, on_delete=models.PROTECT, null=True, blank=True)
    comuna = models.ForeignKey(to=Comuna, on_delete=models.PROTECT, null=True, blank=True)
    fecha_nac = models.DateField(null=True, blank=True)
    ocupacion = models.ForeignKey(to=Ocupacion, on_delete=models.PROTECT, null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, null=True)
    institucion = models.ForeignKey(to=Institucion, on_delete=models.PROTECT, null=True, blank=True)
    n_educacion = models.ForeignKey(Nivel_educacional, on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, default='Inactivo')
    foto = models.URLField(blank=True, null=True)


    areas_interes = models.ManyToManyField(
        'AreaInteres',
        through='UsuarioArea',
        related_name='usuarios'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='usuario_set'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='usuario_permissions_set'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    @property
    def foto_url_firmada(self):
        """
        Genera y devuelve la URL firmada (temporal) de la foto de perfil.
        Si no hay foto o falla la firma, devuelve None.
        """
        # 1. Verificar si el usuario tiene una foto guardada
        if not self.foto:
            return None
        
        try:
            # 2. Llamar a la utilidad de firma, usando la ruta guardada en el campo 'foto'.
            # La URL expira después de 3600 segundos (1 hora)
            return generar_url_firmada(self.foto, expiracion=3600) 
        
        except ConnectionError:
            # Captura si el bucket no se inicializó correctamente
            logger.error(f"Fallo de conexión al intentar firmar la URL: {self.foto}")
            return None
            
        except Exception as e:
            # Capturar otros errores (ej. fallo de comunicación con la API de GCP)
            logger.error(f"Error al generar URL firmada para {self.foto}", exc_info=True)
            return None

    def __str__(self):
        return f"{self.email},  {str(self.id)}"
        

class UsuarioArea(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(to=Usuario, on_delete=models.PROTECT)
    area = models.ForeignKey(to=AreaInteres, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_desactivado = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('usuario', 'area')





