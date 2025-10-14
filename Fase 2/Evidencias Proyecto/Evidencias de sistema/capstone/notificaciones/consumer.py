# home/consumers.py
import json
import logging
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class NotificacionConsumer(WebsocketConsumer):
    def connect(self):
        try:
            self.user = self.scope['user']
            logger.debug(f"👀 Usuario intentando conectar al WS: {self.user}")

            if self.user.is_authenticated:
                # Crear nombre del grupo basado en usuario
                self.group_name = f'notificaciones_{self.user.id}'
                async_to_sync(self.channel_layer.group_add)(
                    self.group_name,
                    self.channel_name
                )
                self.accept()
                logger.info(f"✅ Usuario {self.user.id} aceptado en WebSocket de notificaciones")
            else:
                logger.warning("❌ Usuario no autenticado, cerrando WebSocket")
                self.close()
        except Exception as e:
            logger.exception(f"❌ Error en connect: {e}")
            self.close()

    def disconnect(self, close_code):
        try:
            if hasattr(self, 'group_name'):
                async_to_sync(self.channel_layer.group_discard)(
                    self.group_name,
                    self.channel_name
                )
                logger.info(f"🔌 Usuario {self.user.id} desconectado de notificaciones")
        except Exception as e:
            logger.exception(f"❌ Error en disconnect: {e}")

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"📨 Mensaje recibido de usuario {self.user.id}: {data}")
        except json.JSONDecodeError:
            logger.error("❌ Error decodificando JSON")

    def send_notificacion(self, event):
        try:
            logger.debug(f"📢 Notificación recibida en consumer para enviar: {event}")  # <-- log agregado
            self.send(text_data=json.dumps({
                "id": event["id"],
                "tipo": event.get("tipo", "test"),
                "titulo": event.get("titulo"),
                "mensaje": event.get("mensaje"),
                "datos_extra": event.get("datos_extra", {}),
                "fecha_creacion": event.get("fecha_creacion"),
                "leida": event.get("leida", False)
            }))
            logger.info(f"📨 Notificación enviada al cliente {self.user.id}")
        except Exception as e:
            logger.exception(f"❌ Error enviando notificación: {e}")
