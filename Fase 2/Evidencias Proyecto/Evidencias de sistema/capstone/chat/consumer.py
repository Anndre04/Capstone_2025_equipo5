import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Mensaje

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
        print("mensaje recibido")

        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']

            #se obtiene id del usuario que envia el msj
            if self.scope['user'].is_authenticated:
                sender_id = self.scope['user'].id
            else:
                None

            if sender_id:

                # Se guarda en BD
                message_save = Mensaje.objects.create(
                    user_id=self.user.id,
                    chat_id=self.id,
                    mensaje=message,
                    enviado=True,
                    leido=False
                )
                message_save.save()

                # Sync y enviamos mensaje al chat
                async_to_sync(self.channel_layer.group_send)(
                    self.chat_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': self.user.email,  # si tu campo es email
                        'datetime': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
                        'sender_id': sender_id
                    }
                )
            else:
                print("usuario no autenticado, ignorando mensaje")

        except json.JSONDecodeError as e:
            print("error al decodificad el json: ", e)
        except KeyError as e:
            print('Clave faltan en el json')
        except Exception as e:
            print("error desconocido: ", e)

        
    def chat_message(self, event):
        message = event['message']
        username = event['username']
        datetime = event['datetime']
        sender_id = event['sender_id']

        current_user_id = self.scope['user'].id

        if sender_id != current_user_id:
            self.send(text_data=json.dumps({
            'message': message,
            'username' : username,
            'datetime' : datetime,
        }))