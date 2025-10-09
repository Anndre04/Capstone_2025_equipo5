import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import logging
from .models import Chat, Mensaje

logger = logging.getLogger(__name__)

class ChatConsumer(WebsocketConsumer):
    """
    WebSocket consumer para chats en tiempo real.
    Cada chat tiene su propio grupo para enviar mensajes a todos los participantes.
    """

    def connect(self):
        """Se ejecuta cuando un cliente intenta conectarse."""
        user = self.scope["user"]
        if user.is_anonymous:
            logger.warning("❌ Usuario anónimo intentó conectarse al chat")
            self.close()
            return

        self.user = user
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f"chat_{self.chat_id}"

        # Unirse al grupo del chat
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()  # Aceptar la conexión
        logger.info(f"✅ Usuario {self.user.id} conectado al chat {self.chat_id}")

    def disconnect(self, close_code):
        """Se ejecuta al desconectar el cliente."""
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"🔌 Usuario {self.user.id} desconectado del chat {self.chat_id}")

    def receive(self, text_data):
        """
        Se ejecuta cuando el cliente envía un mensaje.
        Guarda el mensaje en DB y lo reenvía al grupo.
        """
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            if not message:
                return  # Ignorar mensajes vacíos

            # Guardar en DB
            chat_obj = Chat.objects.get(id=self.chat_id)
            mensaje_obj = Mensaje.objects.create(
                chat=chat_obj,
                user=self.user,
                mensaje=message,
                enviado=True,
                leido=False
            )

            # Enviar al grupo para que todos los clientes lo reciban
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',        # Método que se llamará: chat_message
                    'message': message,
                    'username': self.user.nombre,
                    'user_id': self.user.id,
                    'chat_id': self.chat_id,
                    'timestamp': mensaje_obj.timestamp.strftime("%d-%m-%Y %H:%M")
                }
            )

            logger.info(f"💬 Usuario {self.user.id} envió mensaje al chat {self.chat_id}")

        except Chat.DoesNotExist:
            logger.error(f"❌ Chat {self.chat_id} no encontrado")
        except Exception as e:
            logger.error(f"❌ Error en receive: {e}")

    def chat_message(self, event):
        """
        Se ejecuta para enviar mensajes a cada cliente del grupo.
        """
        self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],    # ID del remitente
            'chat_id': event['chat_id'],
            'timestamp': event['timestamp']
        }))


'''class NotificacionConsumer(WebsocketConsumer):
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
        }))'''