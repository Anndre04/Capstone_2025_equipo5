import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tutoria.models import Tutoria
import uuid  # <-- para convertir string a UUID

class TutoriaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Convertir string a UUID
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
                "type": "user_joined",
                "user_id": str(self.user.id),  # <-- UUID a string
                "email": self.user.email
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "user_id": str(self.user.id)  # <-- UUID a string
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "signal",
                "message": data,
                "sender": self.channel_name
            }
        )

    async def signal(self, event):
        if self.channel_name != event["sender"]:
            message = event["message"]
            # Convertir UUID a string si está en el mensaje
            if "user_id" in message:
                message["user_id"] = str(message["user_id"])
            await self.send(text_data=json.dumps(message))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_joined",
            "email": event["email"]
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_left",
            "user_id": str(event["user_id"])  # <-- UUID a string
        }))

    @database_sync_to_async
    def get_tutoria(self):
        return Tutoria.objects.get(id=self.tutoria_id)

    @database_sync_to_async
    def get_tutor_user(self):
        return self.tutoria.tutor.usuario

    @database_sync_to_async
    def get_estudiante_user(self):
        return self.tutoria.estudiante
