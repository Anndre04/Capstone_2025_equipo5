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
        self.id = self.scope['url_route']["kwargs"]['chat_id']
        self.chat_name = 'sala_chat_%s' % self.id
        self.user = self.scope['user']
        print("Conexion establecido con chat_name " + self.chat_name )
        print("Conexion establecido con channel_name " + self.channel_name )

        async_to_sync(self.channel_layer.group_add)(self.chat_name, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        print("desconectado")
        async_to_sync(self.channel_layer.group_discard)(self.chat_name, self.channel_name)


    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            
            # ... (tu código existente de validación y filtro)
            
            if self.scope['user'].is_authenticated:
                sender_id = self.scope['user'].id
                
                # Guardar mensaje en BD (código existente)
                message_save = Mensaje.objects.create(
                    user_id=self.user.id,
                    chat_id=self.id,
                    mensaje=message,  # o mensaje_limpio si usas filtro
                    enviado=True,
                    leido=False
                )
                
                # ✅ EL SIGNAL SE ENCARGARÁ DE LA NOTIFICACIÓN AUTOMÁTICAMENTE
                # Ya no necesitas enviar notificación manual aquí
                
                # Solo enviar el mensaje al grupo del chat
                async_to_sync(self.channel_layer.group_send)(
                    self.chat_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': self.user.get_username(),
                        'datetime': timezone.localtime(timezone.now()).isoformat(),
                        'sender_id': sender_id,
                        'message_id': message_save.id,
                        'chat_id': self.id
                    }
                )
                
        except Exception as e:
            logger.error(f"Error en receive: {e}")

        
    def chat_message(self, event):
        message = event['message']
        username = event['username']
        datetime = event['datetime']
        sender_id = event['sender_id']
        chat_id = event['chat_id']

        current_user_id = self.scope['user'].id

        if sender_id != current_user_id:
            self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'datetime': datetime,
                'chat_id': chat_id  # <-- AGREGAR ESTO
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