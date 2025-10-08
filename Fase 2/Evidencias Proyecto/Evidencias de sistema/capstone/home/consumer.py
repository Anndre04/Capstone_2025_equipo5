# home/consumers.py (o donde tengas tu NotificacionConsumer)
import json
import logging
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Notificacion

logger = logging.getLogger(__name__)

class NotificacionConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.group_name = f'notificaciones_{self.user.id}'
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
            self.accept()
            logger.info(f"Usuario {self.user.id} conectado a notificaciones")
        else:
            self.close()

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )
            logger.info(f"Usuario {self.user.id} desconectado de notificaciones")

    def send_notificacion(self, event):
        """
        Handler para enviar notificaciones al WebSocket
        """
        try:
            self.send(text_data=json.dumps({
                "type": "notificacion",
                "id": event["id"],
                "tipo": event["tipo"],
                "tipo_nombre": event["tipo_nombre"],
                "titulo": event["titulo"],
                "mensaje": event["mensaje"],
                "icono": event["icono"],
                "color": event["color"],
                "fecha_creacion": event["fecha_creacion"],
                "leida": event["leida"],
                "datos_extra": event["datos_extra"]
            }))
        except Exception as e:
            logger.error(f"Error enviando notificación por WebSocket: {e}")