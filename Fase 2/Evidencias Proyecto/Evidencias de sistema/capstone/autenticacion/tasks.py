from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import Signer, SignatureExpired, BadSignature
from django.shortcuts import get_object_or_404
from .models import Usuario  # Asegúrate de importar tu modelo de usuario

signer = Signer()
BASE_URL = "http://localhost:8000"

@shared_task(name='autenticacion.enviar_verificacion')
def enviar_verificacion_email_task(user_id):
    """
    Tarea asíncrona para enviar el correo de verificación.
    Se ejecuta sin el objeto 'request'.
    """
    try:
        # Recuperar el objeto Usuario
        usuario = get_object_or_404(Usuario, id=user_id)
        
        # 1. Generar token (misma lógica que antes)
        token = signer.sign(usuario.id)
        
        # 2. Construir link absoluto con la URL base predefinida

        activation_link = f"{BASE_URL}/auth/activar/{token}/"        
        
        # 3. Enviar correo
        send_mail(
            subject="Activa tu cuenta",
            message=f"Hola {usuario.nombre}.\n\nactiva tu cuenta aquí: {activation_link}",
            from_email=settings.EMAIL_HOST_USER,  # Reemplazar por settings.DEFAULT_FROM_EMAIL
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        print(f"Correo de verificación enviado a {usuario.email}")
        
    except Usuario.DoesNotExist:
        # Si el usuario es eliminado antes de que se ejecute la tarea, fallar silenciosamente
        print(f"Error: Usuario con ID {user_id} no existe para envío de email.")
    except Exception as exc:
        # Reintentar la tarea si falla por un problema de SMTP/red
        raise enviar_verificacion_email_task.retry(exc=exc, countdown=60, max_retries=3)