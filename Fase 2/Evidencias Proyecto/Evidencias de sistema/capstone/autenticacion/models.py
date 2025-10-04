from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

# Create your models here.

class Pais(models.Model):
    nombre = models.CharField(max_length=80)

    def __str__(self):
        return self.nombre

class Region(models.Model):
    nombre = models.CharField(max_length=100)
    numero = models.CharField(max_length=5, unique=True)

    def __str__(self):
        return self.nombre

class Comuna(models.Model):
    nombre = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="comunas")

    def __str__(self):
        return f"{self.nombre} ({self.region.nombre})"
    
class Nivel_educacional(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class AreaInteres(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Ocupacion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Institucion(models.Model):
    nombre = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre
    
class Rol(models.Model):
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
    ocupacion = models.ManyToManyField(to=Ocupacion)    
    institucion = models.ForeignKey(to=Institucion, on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, default='Inactivo')
    foto = models.BinaryField(blank=True, null=True)


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

    def __str__(self):
        return f"{self.email}"
        

class UsuarioArea(models.Model):
    usuario = models.ForeignKey(to=Usuario, on_delete=models.PROTECT)
    area = models.ForeignKey(to=AreaInteres, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_desactivado = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('usuario', 'area')





