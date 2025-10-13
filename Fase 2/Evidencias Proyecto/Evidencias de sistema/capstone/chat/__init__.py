# chat/__init__.py
default_app_config = 'chat.apps.ChatConfig'

# chat/apps.py
from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
    
    def ready(self):
        import notificaciones.signals  # ← IMPORTAR LOS SIGNALS