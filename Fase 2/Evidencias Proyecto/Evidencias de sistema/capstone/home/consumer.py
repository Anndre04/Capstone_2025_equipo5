# home/consumers.py
import json
import logging
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class NotificacionConsumer(WebsocketConsumer):
    def connect(self):
        # Verificar autenticación
        if self.scope["user"].is_anonymous:
            logger.warning("❌ Usuario anónimo intentó conectar a notificaciones")
            self.close()
            return
        
        self.user = self.scope["user"]
        self.group_name = f'notificaciones_{self.user.id}'
        
        # Unirse al grupo de notificaciones del usuario
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        
        self.accept()
        logger.info(f"✅ Usuario {self.user.id} conectado a notificaciones")

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )
            logger.info(f"🔌 Usuario {self.user.id} desconectado de notificaciones")

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"📨 Mensaje recibido de usuario {self.user.id}: {data}")
        except json.JSONDecodeError:
            logger.error("❌ Error decodificando JSON")

    def send_notificacion(self, event):
        """Handler para enviar notificaciones al WebSocket"""
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
            logger.error(f"❌ Error enviando notificación: {e}")