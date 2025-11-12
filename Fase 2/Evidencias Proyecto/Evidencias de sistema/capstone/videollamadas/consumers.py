import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tutoria.models import Tutoria
import uuid

class TutoriaConsumer(AsyncWebsocketConsumer):
    
    # --- Métodos de Conexión y Desconexión ---
    
    async def connect(self):
        # ... (Tu lógica de conexión existente) ...
        self.tutoria_id = uuid.UUID(self.scope['url_route']['kwargs']['tutoria_id'])
        self.user = self.scope['user']

        self.tutoria = await self.get_tutoria()
        tutor_user = await self.get_tutor_user()
        estudiante_user = await self.get_estudiante_user()

        if self.user != tutor_user and self.user != estudiante_user:
            await self.close()
            return

        self.room_group_name = f"tutoria_{self.tutoria_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notificar conexión
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.joined", # Usamos user.joined para diferenciar del tipo de mensaje cliente
                "email": self.user.email
            }
        )
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.left", # Usamos user.left para diferenciar del tipo de mensaje cliente
                "user_id": str(self.user.id)
            }
        )

    # --- Manejo de Mensajes Recibidos (CLAVE: Optimización) ---
    
    async def receive(self, text_data):
        """Maneja los mensajes entrantes del WebSocket (Offer, Answer, ICE, Chat)."""
        data = json.loads(text_data)
        message_type = data.get("type")
        
        # 1. Si es un mensaje de señalización (WebRTC)
        if message_type in ["offer", "answer", "ice-candidate"]:
            # Reenviar el mensaje de señalización tal cual al otro miembro del grupo
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "signal.message", # Nuevo handler más directo
                    "message": data,
                    "sender_channel": self.channel_name # Usamos sender_channel para evitar enviarlo a sí mismo
                }
            )
            
        # 2. Si es un mensaje de unión (Solo se usa al inicio, pero lo mantenemos)
        elif message_type == "join":
            # Si el cliente se une, simplemente confirma la conexión (la notificación ya se envió en connect)
            # Podríamos enviar una lista de usuarios conectados, pero por simplicidad, no hacemos nada más.
            pass
            
        # 3. Si es un mensaje de Chat (DataChannel)
        elif message_type == "chat":
            # Reenviar el mensaje de chat al grupo
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message", # Handler específico para chat
                    "message": data,
                    "sender_channel": self.channel_name
                }
            )
        # 3. CLAVE: Mensajes de Coordinación de Pantalla
        elif message_type in ["screen_share_start", "screen_share_stop"]:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "screen.status", # Nuevo handler
                    "message": data,
                    "sender_channel": self.channel_name
                }
            )
        
        else:
            print(f"Tipo de mensaje desconocido: {message_type}")


    # --- Handlers de Grupo (Envío a Cliente) ---

    async def signal_message(self, event):
        """Reenvía mensajes de señalización (SDP, ICE) al receptor."""
        # Evita que el remitente se envíe el mensaje a sí mismo
        if self.channel_name != event["sender_channel"]:
            await self.send(text_data=json.dumps(event["message"]))

    async def chat_message(self, event):
        """Reenvía mensajes de chat (DataChannel) al receptor."""
        if self.channel_name != event["sender_channel"]:
            await self.send(text_data=json.dumps(event["message"]))

    async def user_joined(self, event):
        """Notifica que un usuario se unió."""
        await self.send(text_data=json.dumps({
            "type": "user_joined",
            "email": event["email"]
        }))

    async def user_left(self, event):
        """Notifica que un usuario salió."""
        await self.send(text_data=json.dumps({
            "type": "user_left",
            "user_id": str(event["user_id"])
        }))

    async def screen_status(self, event):
        """Reenvía mensajes de inicio/fin de compartición de pantalla."""
        if self.channel_name != event["sender_channel"]:
            await self.send(text_data=json.dumps(event["message"]))

    async def evaluacion_publicada(self, event):
        """Envía el ID de la evaluación publicada a los clientes."""
        evaluacion_id = event['evaluacion_id']

        # Envía el mensaje de vuelta al WebSocket del cliente
        await self.send(text_data=json.dumps({
            'type': 'evaluacion_publicada', # Usamos el mismo tipo para que JS lo reconozca
            'evaluacion_id': evaluacion_id
        }))
        
    # --- Métodos de Base de Datos ---
    
    @database_sync_to_async
    def get_tutoria(self):
        return Tutoria.objects.get(id=self.tutoria_id)

    @database_sync_to_async
    def get_tutor_user(self):
        return self.tutoria.tutor.usuario

    @database_sync_to_async
    def get_estudiante_user(self):
        return self.tutoria.estudiante