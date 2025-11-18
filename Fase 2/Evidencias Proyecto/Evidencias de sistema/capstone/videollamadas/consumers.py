import json
import logging
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
# NOTA: Asegúrate de importar tu modelo Tutoria aquí
from tutoria.models import Tutoria 

# Configuración de Logging
logger = logging.getLogger(__name__)

class TutoriaConsumer(AsyncWebsocketConsumer):
    pc = None 

    # --- Conexión y desconexión ---
    async def connect(self):
        # 1. Validación segura de UUID y gestión de errores
        try:
            self.tutoria_id = uuid.UUID(self.scope['url_route']['kwargs']['tutoria_id'])
        except ValueError:
            logger.error("ID de tutoría inválido.")
            await self.close()
            return

        self.user = self.scope['user']

        # 2. Validación de la tutoría y usuarios (Manejo de Tutoria.DoesNotExist)
        self.tutoria = await self.get_tutoria()
        if not self.tutoria:
             logger.warning(f"Tutoria ID {self.tutoria_id} no encontrada. Cerrando conexión.")
             await self.close()
             return

        tutor_user = await self.get_tutor_user()
        estudiante_user = await self.get_estudiante_user()

        # 3. Control de acceso
        if self.user != tutor_user and self.user != estudiante_user:
            logger.warning(f"Usuario {self.user.id} intentó acceder a tutoria {self.tutoria_id} sin permiso.")
            await self.close()
            return

        # 4. Setup de Grupo y Aceptación
        self.room_group_name = f"tutoria_{self.tutoria_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info(f"Usuario {self.user.id} conectado a {self.room_group_name}.")

        # Notificar conexión (Incluye sender_channel para evitar eco)
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "user.joined", "email": self.user.email, "sender_channel": self.channel_name}
        )

    async def disconnect(self, close_code):
        user_id_str = str(self.user.id)
        room_name = self.room_group_name
        
        logger.info(f"Usuario {user_id_str} desconectado de {room_name} (Código: {close_code}).")
            
        await self.channel_layer.group_discard(room_name, self.channel_name)
        
        # Notificar desconexión (Incluye sender_channel)
        await self.channel_layer.group_send(
            room_name,
            {"type": "user.left", "user_id": user_id_str, "sender_channel": self.channel_name}
        )

    # --- Manejo de mensajes recibidos (Reenvío consolidado) ---
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
        except json.JSONDecodeError:
            logger.error(f"Error decodificando JSON: {text_data}")
            return

        # Añadir sender_channel para evitar eco
        data["sender_channel"] = self.channel_name

        # --- Señalización WebRTC ---
        if message_type in ["offer", "answer"]:
            sdp_obj = data.get("sdp", {})
            if isinstance(sdp_obj, dict):
                data["sdp"] = sdp_obj.get("sdp", "")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "forward.message", "content": data}
            )

        elif message_type == "ice-candidate":
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "forward.message", "content": data}
            )

        # --- Chat ---
        elif message_type == "chat":
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "forward.message", "content": data}
            )

        # --- Screen sharing ---
        elif message_type in ["screen_share_start", "screen_share_stop"]:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "forward.message", "content": data}
            )

        # --- Evaluación publicada ---
        elif message_type == "evaluacion_publicada":
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "evaluacion.publicada", "content": data}
            )

        # --- Heartbeat / Pong ---
        elif message_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

        # --- Usuario recién conectado ---
        elif message_type == "join":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user.joined",
                    "email": self.user.email,
                    "sender_channel": self.channel_name
                }
            )

        # --- Usuario que recarga la página ---
        elif message_type == "reconnect_request":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user.reconnect_request",
                    "sender_channel": self.channel_name,
                    "user_id": str(self.user.id)
                }
            )

        else:
            logger.warning(f"Tipo de mensaje desconocido: {message_type}")


    # --- Handler del grupo para reconexión ---
    async def user_reconnect_request(self, event):
        if self.channel_name != event.get("sender_channel"):
            await self.send(text_data=json.dumps({
                "type": "reconnect_request",
                "user_id": event.get("user_id")
            }))


    async def forward_message(self, event):
        """Handler genérico para reenviar mensajes de señalización, chat y control."""
        content = event["content"]
        # Filtra por sender_channel para evitar el eco
        if self.channel_name != content.get("sender_channel"):
            await self.send(text_data=json.dumps(content)) 

    async def user_joined(self, event):
        """Notifica que un usuario se unió, con prevención de eco."""
        if self.channel_name != event.get("sender_channel"):
            await self.send(text_data=json.dumps({
                "type": "user_joined",
                "email": event.get("email", "Usuario")
            }))

    async def user_left(self, event):
        """Notifica que un usuario se fue, con prevención de eco."""
        if self.channel_name != event.get("sender_channel"):
             await self.send(text_data=json.dumps({
                "type": "user_left",
                "user_id": str(event.get("user_id"))
            }))

    # En videollamadas/consumers.py

    async def evaluacion_publicada(self, event):
        """Handler para la publicación de evaluaciones."""
        
        evaluacion_id = event.get('evaluacion_id')
        sender_channel = event.get("sender_channel")

        if self.channel_name != sender_channel and evaluacion_id:
            await self.send(text_data=json.dumps({
                'type': 'evaluacion_publicada',
                'evaluacion_id': evaluacion_id
            }))
        else:
            # Esto podría registrar un error si el evaluacion_id falta
            logging.debug(f"DEBUG: Mensaje de evaluación ignorado. self.channel_name: {self.channel_name}, sender_channel: {sender_channel}, id: {evaluacion_id}")
            
    # --- Métodos de Base de Datos ---
    @database_sync_to_async
    def get_tutoria(self):
        try:
            # Retorna None si no existe la tutoría
            return Tutoria.objects.get(id=self.tutoria_id)
        except Tutoria.DoesNotExist:
            return None

    @database_sync_to_async
    def get_tutor_user(self):
        # Accede de forma segura al usuario del tutor
        return getattr(getattr(self.tutoria, 'tutor', None), 'usuario', None)

    @database_sync_to_async
    def get_estudiante_user(self):
        # Accede de forma segura al usuario del estudiante
        return getattr(self.tutoria, 'estudiante', None)