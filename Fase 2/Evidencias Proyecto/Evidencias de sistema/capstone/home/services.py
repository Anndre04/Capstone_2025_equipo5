# home/services.py
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notificacion, TipoNotificacion
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    
    @staticmethod
    def get_tipo_by_codigo(codigo):
        """Obtiene un tipo de notificación por su código"""
        try:
            return TipoNotificacion.objects.get(codigo=codigo, activo=True)
        except TipoNotificacion.DoesNotExist:
            logger.error(f"Tipo de notificación no encontrado: {codigo}")
            raise ValueError(f"Tipo de notificación no encontrado: {codigo}")
    
    @staticmethod
    def crear_notificacion(usuario, codigo_tipo, titulo, mensaje, datos_extra=None):
        """
        Crea una notificación y la envía via WebSocket
        """
        with transaction.atomic():
            try:
                tipo = NotificationService.get_tipo_by_codigo(codigo_tipo)
                
                notificacion = Notificacion.objects.create(
                    usuario=usuario,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_extra=datos_extra or {}
                )
                
                # Enviar via WebSocket (si está conectado)
                NotificationService._enviar_websocket(notificacion)
                
                logger.info(f"Notificación creada: {notificacion}")
                return notificacion
                
            except Exception as e:
                logger.error(f"Error creando notificación: {e}")
                raise
    
    @staticmethod
    def _enviar_websocket(notificacion):
        """
        Envía la notificación via WebSocket al usuario
        """
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
                
            group_name = f"notificaciones_{notificacion.usuario.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notificacion",
                    "id": notificacion.id,
                    "tipo": notificacion.tipo.codigo,
                    "tipo_nombre": notificacion.tipo.nombre,
                    "titulo": notificacion.titulo,
                    "mensaje": notificacion.mensaje,
                    "icono": notificacion.tipo.icono,
                    "color": notificacion.tipo.color,
                    "fecha_creacion": notificacion.fecha_creacion.isoformat(),
                    "leida": notificacion.leida,
                    "datos_extra": notificacion.datos_extra or {}
                }
            )
            logger.debug(f"Notificación enviada por WebSocket a usuario {notificacion.usuario.id}")
            
        except Exception as e:
            logger.error(f"Error enviando WebSocket: {e}")

    @staticmethod
    def marcar_como_leida(notificacion_id, usuario):
        """
        Marca una notificación como leída
        """
        try:
            notificacion = Notificacion.objects.get(id=notificacion_id, usuario=usuario)
            notificacion.leida = True
            notificacion.save()
            return notificacion
        except Notificacion.DoesNotExist:
            raise ValueError("Notificación no encontrada")

    @staticmethod
    def obtener_no_leidas(usuario):
        """
        Obtiene el conteo de notificaciones no leídas
        """
        return Notificacion.objects.filter(usuario=usuario, leida=False).count()