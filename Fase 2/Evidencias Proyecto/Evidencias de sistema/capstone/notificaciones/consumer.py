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
            print("👀 Usuario en connect:", self.user)
            if self.user.is_authenticated:
                self.group_name = f'notificaciones_{self.user.id}'
                async_to_sync(self.channel_layer.group_add)(
                    self.group_name,
                    self.channel_name
                )
                self.accept()
                print(f"✅ Usuario {self.user.id} aceptado en WebSocket")
            else:
                print("❌ Usuario no autenticado, cerrando WebSocket")
                self.close()
        except Exception as e:
            print("❌ Error en connect:", e)
            self.close()

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
        try:
            print("📢 Llega notificación al consumer:", event)  # Solo para debug
            self.send(text_data=json.dumps({
                "id": event["id"],
                "tipo": event.get("tipo", "test"),
                "titulo": event.get("titulo"),
                "mensaje": event.get("mensaje"),
                "datos_extra": event.get("datos_extra", {}),
                "fecha_creacion": event.get("fecha_creacion"),
                "leida": event.get("leida", False)
            }))
        except Exception as e:
            print("❌ Error enviando notificación:", e)