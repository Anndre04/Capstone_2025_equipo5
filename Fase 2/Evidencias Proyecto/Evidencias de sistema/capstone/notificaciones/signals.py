# home/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from notificaciones.services import NotificationService
import logging
from chat.models import Mensaje
from tutoria.models import ComentarioPredefinido, Solicitud, Tutoria

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
                'chat_id': str(chat.id),
                'sender_id': str(usuario_remitente.id),
                'sender_name': usuario_remitente.nombre,
                'mensaje_id': str(instance.id),
                'url': 'chat'
            }
        )
        logger.info(f"Notificación de mensaje enviada a usuario {usuario_destino.id}")

    except Exception as e:
        logger.error(f"Error en notificación de mensaje: {e}")

@receiver(post_save, sender=Solicitud)
def notificar_nueva_solicitud_alumno(sender, instance, created, **kwargs):
    if not created:
        return

    # 🔍 SOLO SI el tipo de solicitud es "alumno"
    if instance.tipo.nombre.lower() != "alumno":
        return

    try:
        NotificationService.crear_notificacion(
            usuario=instance.usuarioreceive,
            codigo_tipo="solicitud_alumno",
            titulo="Nueva solicitud recibida",
            mensaje=f"{instance.usuarioenvia.nombre} te ha enviado una solicitud de alumno.",
            datos_extra={
                "solicitud_id": str(instance.id),
                "url": f"/tutoria/solicitudesprof/{instance.usuarioreceive.id}",
            },
        )

        logger.info(f"📨 Notificación enviada al tipo 'alumno' para {instance.usuarioreceive.nombre}")

    except Exception as e:
        logger.error(f"❌ Error en notificación de solicitud alumno: {e}")


@receiver(post_save, sender=Tutoria)
def notificacion_tutoria_completada(sender, instance, created, **kwargs):
    """
    Envía notificación cuando la tutoría cambia a 'Completada'.
    Cada usuario recibe su propia notificación si aún no la tiene.
    """
    if instance.estado != "Completada":
        return  # Solo notificar si la tutoría está completada

    try:
        comentarios_predefinidos = [
            {"id": str(c.id), "comentario": c.comentario}
            for c in ComentarioPredefinido.objects.all()
        ]
        usuarios_a_notificar = [instance.tutor.usuario, instance.estudiante]

        for usuario in usuarios_a_notificar:
            # Solo crear la notificación si no existe para este usuario
            if not NotificationService.notificacion_existente(instance.id, 'tutoria_finalizada', usuario):
                NotificationService.crear_notificacion(
                    usuario=usuario,
                    codigo_tipo='tutoria_finalizada',
                    titulo='Tutoría finalizada',
                    mensaje='La tutoría ha finalizado.',
                    datos_extra={
                        'tutoria_id': str(instance.id),
                        'url': f'tutoria/tutoria/{instance.id}',
                        'comentarios_predefinidos': comentarios_predefinidos
                    }
                )
                logger.info(f"Notificación de tutoría finalizada enviada a usuario {usuario.id}")
            else:
                logger.info(f"Notificación ya existente para tutoría {instance.id}, usuario {usuario.id}")

    except Exception as e:
        logger.error(f"Error en notificación de tutoría: {e}")
