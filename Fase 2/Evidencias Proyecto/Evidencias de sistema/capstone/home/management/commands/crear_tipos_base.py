# home/management/commands/crear_tipos_base.py
from django.core.management.base import BaseCommand
from home.models import TipoNotificacion

class Command(BaseCommand):
    help = 'Crea los tipos de notificación base del sistema'

    def handle(self, *args, **options):
        tipos_base = [
            {
                'nombre': 'Nuevo Mensaje',
                'codigo': 'nuevo_mensaje',
                'descripcion': 'Tienes un nuevo mensaje en el chat',
                'icono': 'bi-chat-text',
                'color': 'primary'
            },
            {
                'nombre': 'Solicitud de Tutoría',
                'codigo': 'solicitud_tutoria', 
                'descripcion': 'Nueva solicitud de tutoría recibida',
                'icono': 'bi-journal-plus',
                'color': 'info'
            },
            {
                'nombre': 'Solicitud Aceptada',
                'codigo': 'solicitud_aceptada',
                'descripcion': 'Tu solicitud de tutoría fue aceptada',
                'icono': 'bi-check-circle',
                'color': 'success'
            },
            {
                'nombre': 'Solicitud Rechazada',
                'codigo': 'solicitud_rechazada',
                'descripcion': 'Tu solicitud de tutoría fue rechazada', 
                'icono': 'bi-x-circle',
                'color': 'warning'
            },
            {
                'nombre': 'Mensaje del Sistema',
                'codigo': 'sistema',
                'descripcion': 'Mensaje importante del sistema',
                'icono': 'bi-info-circle',
                'color': 'dark'
            }
        ]

        creados = 0
        for tipo_data in tipos_base:
            tipo, created = TipoNotificacion.objects.get_or_create(
                codigo=tipo_data['codigo'],
                defaults=tipo_data
            )
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Tipo creado: {tipo.nombre}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'🎉 Se crearon {creados} tipos de notificación')
        )