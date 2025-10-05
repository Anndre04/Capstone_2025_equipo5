from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Mensaje
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender=Mensaje)
def enviar_notificacion(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    for usuario in instance.chat.users.exclude(id=instance.user.id):
        group_name = f"notificaciones_{usuario.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notificacion",  # coincide con el método del consumer
                "chat_id": instance.chat.id,
                "mensaje": instance.mensaje,
                "remitente": instance.user.email,
                "timestamp": instance.timestamp.strftime("%H:%M %d/%m/%Y")
            }
        )
