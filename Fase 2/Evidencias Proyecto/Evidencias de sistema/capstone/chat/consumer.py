import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Mensaje
from .filters import filtro_lenguaje
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        # Verificar autenticación
        if self.scope["user"].is_anonymous:
            logger.warning("❌ Usuario anónimo intentó conectar al chat")
            self.close()
            return
        
        self.user = self.scope["user"]
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        
        # Unirse al grupo del chat
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        self.accept()
        logger.info(f"✅ Usuario {self.user.id} conectado al chat {self.chat_id}")

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"🔌 Usuario {self.user.id} desconectado del chat {self.chat_id}")

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            
            logger.info(f"💬 Usuario {self.user.id} envió mensaje: {message}")
            
            # Enviar mensaje al grupo del chat
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.user.username,
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error en receive: {e}")

    def chat_message(self, event):
        """Handler para mensajes del chat"""
        self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
        }))
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
        else:
            self.close()

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )

    # Handler síncrono para la notificación
    def send_notificacion(self, event):
        self.send(text_data=json.dumps({
            "mensaje": event["mensaje"],
            "chat_id": event["chat_id"],
            "remitente": event["remitente"],
            "timestamp": event["timestamp"]
        }))