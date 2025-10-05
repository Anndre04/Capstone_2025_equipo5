from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Chat, Mensaje

def chat(request):
    user = request.user  # Usuario logeado

    # Traer todos los chats donde el usuario participa
    chats = Chat.objects.filter(users=user).order_by('-fecha_creacion')

    # Preparar datos para mostrar en la lista lateral
    chat_data = []
    for chat in chats:
        # Obtener el otro usuario del chat 1:1
        contacto_user = chat.users.exclude(id=user.id).first()
        contacto = f"{contacto_user.nombre} {contacto_user.p_apellido}" if contacto_user else "Desconocido"
        
        # Último mensaje del chat
        ultimo_mensaje = chat.mensaje_set.order_by('-timestamp').first()
        ultimo_texto = ultimo_mensaje.mensaje if ultimo_mensaje else ''

        
        chat_data.append({
            'id': chat.id,
            'contacto': str(contacto),
            'ultimo_mensaje': ultimo_texto,  # <-- esto permite mostrarlo en el template
        })

        # Si hay chats, cargar la primera conversación
    primera_chat_id = chat_data[0]['id'] if chat_data else None

    return render(request, 'chat.html', {
        'chat_data': chat_data,
        'primera_chat_id': primera_chat_id,
    })


@login_required
def mensajes_view(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id)
        N = 20  # cantidad de mensajes a traer
        mensajes = chat.mensaje_set.all().order_by('-timestamp')[:N]  # últimos N mensajes
        mensajes = reversed(mensajes)  # ordenarlos cronológicamente

        data = {
            "mensajes": [
                {
                    "contenido": m.mensaje,
                    "fecha": m.timestamp.strftime("%H:%M %d/%m/%Y"),
                    "es_mio": m.user.id == request.user.id
                } for m in mensajes
            ]
        }
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)