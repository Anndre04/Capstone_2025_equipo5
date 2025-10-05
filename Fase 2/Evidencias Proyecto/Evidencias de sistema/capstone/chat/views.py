from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Chat, Mensaje
from autenticacion.models import Usuario

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

        no_leidos = chat.mensaje_set.filter(leido=False).exclude(user=user).count()

        
        chat_data.append({
            'id': chat.id,
            'contacto': str(contacto),
            'ultimo_mensaje': ultimo_texto,
            'no_leidos': no_leidos
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
    
def crear_chat(request, user_id):
    user = request.user
    otro_usuario = get_object_or_404(Usuario, id=user_id)

    # Buscar si ya existe un chat 1:1 entre ambos
    chat_existente = Chat.objects.filter(users=user).filter(users=otro_usuario).first()

    if chat_existente:
        chat = chat_existente
    else:
        # Crear un nuevo chat solo si no existe
        chat = Chat.objects.create()
        chat.users.add(user, otro_usuario)
        chat.save()

    return redirect('chat') 

@login_required
def marcar_leidos(request, chat_id):
    print("💡 Llamada a marcar_leidos:", request.method, "Usuario:", request.user)

    if request.method == 'POST' and request.user.is_authenticated:
        try:
            chat = Chat.objects.get(id=chat_id)
            print("💡 Chat encontrado:", chat.id)

            mensajes_no_leidos = chat.mensaje_set.filter(leido=False).exclude(user=request.user)
            print(f"💡 Mensajes no leídos encontrados: {mensajes_no_leidos.count()}")

            updated_count = mensajes_no_leidos.update(leido=True)
            print(f"💡 Mensajes marcados como leídos: {updated_count}")

            return JsonResponse({'status': 'ok', 'marcados': updated_count})
        except Chat.DoesNotExist:
            print("❌ Chat no encontrado")
            return JsonResponse({'status': 'error', 'message': 'Chat no encontrado'}, status=404)

    print("❌ Método no permitido o usuario no autenticado")
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)