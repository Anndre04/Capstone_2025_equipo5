from celery import shared_task
from django.conf import settings
from django.core.signing import Signer, SignatureExpired, BadSignature
from django.shortcuts import get_object_or_404
from .models import Usuario  # Asegúrate de importar tu modelo de usuario
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


signer = Signer()
BASE_URL = "http://localhost:8000"

@shared_task(name='autenticacion.enviar_verificacion')
def enviar_verificacion_email_task(user_id):
    """
    Tarea asíncrona para enviar el correo de verificación con HTML personalizado.
    """
    try:
        # Recuperar el usuario
        usuario = get_object_or_404(Usuario, id=user_id)

        # Generar token
        token = signer.sign(usuario.id)

        # Construir link de activación
        activation_link = f"{BASE_URL}/auth/activar/{token}/"

        # Renderizar plantilla HTML personalizada
        html_content = render_to_string(
            'emails/activar_cuenta.html',  # tu plantilla HTML
            {
                'usuario': usuario,
                'activation_link': activation_link,
                'protocol': 'http',
                'domain': 'localhost:8000',  # o tu dominio real en producción
            }
        )

        # Texto plano (opcional, para clientes de correo que no leen HTML)
        text_content = f"Hola {usuario.nombre}, activa tu cuenta aquí: {activation_link}"

        # Crear email
        email = EmailMultiAlternatives(
            subject="Activa tu cuenta - TutorPlus",
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[usuario.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        print(f"Correo de verificación enviado a {usuario.email}")

    except Usuario.DoesNotExist:
        print(f"Error: Usuario con ID {user_id} no existe para envío de email.")
    except Exception as exc:
        # Reintentar la tarea si falla por un problema de SMTP/red
        raise enviar_verificacion_email_task.retry(exc=exc, countdown=60, max_retries=3)