import os
from celery import Celery

# 1. Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')

# 2. Crear la instancia de Celery
app = Celery('capstone')

# 3. Configuración desde Django settings (CELERY_...)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. Descubrir tareas automáticamente
# Celery buscará un archivo tasks.py en todas las apps instaladas
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')