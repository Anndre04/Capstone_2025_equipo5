# chat/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from home.services import NotificationService
from .models import Mensaje
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Mensaje)
def enviar_notificacion_mensaje(sender, instance, created, **kwargs):
    """
    Reemplaza la notificación vieja por el nuevo sistema global
    """
    if not created:
        return

    try:
        chat = instance.chat
        usuario_remitente = instance.user
        
        # Obtener el otro usuario del chat 1:1
        usuario_destino = chat.users.exclude(id=usuario_remitente.id).first()
        
        if not usuario_destino:
            logger.warning(f"No se encontró usuario destino para chat {chat.id}")
            return

        # ✅ USAR EL NUEVO SISTEMA DE NOTIFICACIONES
        NotificationService.crear_notificacion(
            usuario=usuario_destino,
            codigo_tipo='nuevo_mensaje',
            titulo=f'Nuevo mensaje de {usuario_remitente.nombre}',
            mensaje=instance.mensaje,
            datos_extra={
                'chat_id': chat.id,
                'sender_id': usuario_remitente.id,
                'sender_name': usuario_remitente.nombre,
                'mensaje_id': instance.id
            }
        )
        
        logger.info(f"Notificación de mensaje enviada a {usuario_destino.id}")

    except Exception as e:
        logger.error(f"Error en notificación de mensaje: {e}")