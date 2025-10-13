# home/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from notificaciones.services import NotificationService
import logging
from chat.models import Mensaje
from tutoria.models import Solicitud

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Mensaje)
def notificacion_mensaje_chat(sender, instance, created, **kwargs):
    if not created:
        return  # Solo notificamos al crear

    try:
        chat = instance.chat
        usuario_remitente = instance.user

        # Obtener el otro usuario del chat 1:1
        usuario_destino = chat.users.exclude(id=usuario_remitente.id).first()
        if not usuario_destino:
            logger.warning(f"No se encontró usuario destino para chat {chat.id}")
            return

        # Usamos el servicio general de notificaciones
        NotificationService.crear_notificacion(
            usuario=usuario_destino,
            codigo_tipo='nuevo_mensaje',
            titulo=f'Nuevo mensaje de {usuario_remitente.nombre}',
            mensaje=instance.mensaje,
            datos_extra={
                'chat_id': chat.id,
                'sender_id': usuario_remitente.id,
                'sender_name': usuario_remitente.nombre,
                'mensaje_id': instance.id,
                'url': 'chat'
            }
        )
        logger.info(f"Notificación de mensaje enviada a usuario {usuario_destino.id}")

    except Exception as e:
        logger.error(f"Error en notificación de mensaje: {e}")

@receiver(post_save, sender=Solicitud)
def notificar_nueva_solicitud(sender, instance, created, **kwargs):
    """
    Envía una notificación cuando se crea una nueva solicitud.
    """
    if created:
        try:
            print(f"✅ Nueva solicitud creada por {instance.usuarioenvia.nombre} para {instance.usuarioreceive.nombre}")
            # Crear notificación
            NotificationService.crear_notificacion(
                usuario=instance.usuarioreceive,  # el que recibe la solicitud
                codigo_tipo="solicitud_recibida",
                titulo="Nueva solicitud recibida",
                mensaje=f"{instance.usuarioenvia.nombre} te ha enviado una solicitud.",
                datos_extra={
                    "solicitud_id": instance.id,
                    "url" : f"tutoria/solicitudesprof/{instance.usuarioreceive.id}"
                    },
            )

            logger.info(f"📨 Notificación enviada a {instance.usuarioreceive.nombre}")
        except Exception as e:
            logger.error(f"❌ Error en notificación de solicitud: {e}")