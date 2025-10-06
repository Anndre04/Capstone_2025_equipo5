from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from datetime import date, datetime
import re
from .models import Usuario, Pais, Region, Comuna, Ocupacion, AreaInteres

def validar_edad(fecha_nacimiento):
    """
    Valida que la edad esté entre 13 y 120 años
    y que no sea una fecha futura
    """
    if not fecha_nacimiento:
        return
    
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    
    # Validar edad mínima (13 años)
    if edad < 13:
        raise ValidationError('Debes tener al menos 13 años para registrarte.')
    
    # Validar edad máxima (120 años)
    if edad > 120:
        raise ValidationError('Por favor ingresa una fecha de nacimiento válida.')
    
    # Validar que no sea fecha futura
    if fecha_nacimiento > hoy:
        raise ValidationError('La fecha de nacimiento no puede ser futura.')

def validar_solo_letras(valor):
    """
    Valida que el valor contenga solo letras y espacios
    """
    if valor:
        # Permitir letras, espacios y algunos caracteres especiales comunes en nombres
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', valor):
            raise ValidationError('Este campo solo puede contener letras y espacios.')

def validar_rut(valor):
    """
    Valida que el RUT no exceda los 18 caracteres y tenga formato básico
    """
    if valor:
        # Validar longitud máxima
        if len(valor) > 18:
            raise ValidationError('El RUT no puede tener más de 18 caracteres.')
        
        # Validar formato básico (números, k, K, guiones y puntos)
        if not re.match(r'^[0-9\.\-kK]+$', valor):
            raise ValidationError('El RUT solo puede contener números, puntos, guiones y la letra K.')

class RegistroForm(UserCreationForm):
    nombre = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm', 
            'placeholder': 'Tu nombre'
        })
    )
    p_apellido = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm', 
            'placeholder': 'Primer apellido'
        })
    )
    s_apellido = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm', 
            'placeholder': 'Segundo apellido'
        })
    )
    run = forms.CharField(
        max_length=10,  # Cambiado de 10
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm', 
            'placeholder': 'RUN - Máx. 18 caracteres'
        })
    )
    fecha_nac = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm', 
            'type': 'date'
        }),
        help_text="Debes tener al menos 13 años"
    )
    
    pais = forms.ModelChoiceField(
        queryset=Pais.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    comuna = forms.ModelChoiceField(
        queryset=Comuna.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    
    ocupacion = forms.ModelMultipleChoiceField(
        queryset=Ocupacion.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-control-sm',
            'size': '3'
        })
    )
    areas_interes = forms.ModelMultipleChoiceField(
        queryset=AreaInteres.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-control-sm',
            'size': '3'
        })
    )

    class Meta:
        model = Usuario
        fields = [
            'email', 'nombre', 'p_apellido', 's_apellido', 'run',
            'fecha_nac', 'pais', 'region', 'comuna', 'ocupacion', 
            'areas_interes', 'password1', 'password2'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-sm', 
                'placeholder': 'tu@email.com'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Contraseña'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Confirmar contraseña'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_nombre(self):
        """
        Validación personalizada para el nombre
        """
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            validar_solo_letras(nombre)
        return nombre

    def clean_p_apellido(self):
        """
        Validación personalizada para el primer apellido
        """
        p_apellido = self.cleaned_data.get('p_apellido')
        if p_apellido:
            validar_solo_letras(p_apellido)
        return p_apellido

    def clean_s_apellido(self):
        """
        Validación personalizada para el segundo apellido
        """
        s_apellido = self.cleaned_data.get('s_apellido')
        if s_apellido:
            validar_solo_letras(s_apellido)
        return s_apellido

    def clean_run(self):
        """
        Validación personalizada para el RUT
        """
        run = self.cleaned_data.get('run')
        if run:
            validar_rut(run)
        return run

    def clean_fecha_nac(self):
        """
        Validación personalizada para la fecha de nacimiento
        """
        fecha_nac = self.cleaned_data.get('fecha_nac')
        
        # Si el usuario ingresó una fecha, validamos
        if fecha_nac:
            validar_edad(fecha_nac)
        
        return fecha_nac

    def clean(self):
        """
        Validación adicional del formulario completo
        """
        cleaned_data = super().clean()
        
        # Puedes agregar aquí validaciones que involucren múltiples campos
        # Por ejemplo, validar que si se selecciona región, también se seleccione país
        
        return cleaned_data

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'tu@email.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Tu contraseña',
            'autocomplete': 'current-password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Correo Electrónico'