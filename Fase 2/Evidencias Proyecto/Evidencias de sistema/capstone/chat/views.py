import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Chat, Mensaje
from autenticacion.models import Usuario
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

@login_required
def chat(request):
    user = request.user
    chats = Chat.objects.filter(users=user).order_by('-fecha_creacion')

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
            'id': str(chat.id),  # UUID -> str para JSON
            'contacto': str(contacto),
            'ultimo_mensaje': ultimo_texto,
            'no_leidos': no_leidos
        })

    # PRIORIDAD: 1. Sesión, 2. Primer chat, 3. Ninguno
    primera_chat_id = None
    if 'ultimo_chat_id' in request.session:
        primera_chat_id = request.session['ultimo_chat_id']
        del request.session['ultimo_chat_id']
    elif chat_data:
        primera_chat_id = chat_data[0]['id']

    return render(request, 'chat.html', {
        'chat_data': chat_data,
        'primera_chat_id': primera_chat_id,
    })


@login_required
def mensajes_view(request, chat_id):  # chat_id ya es UUID
    MENSAJES_POR_PAGINA = 30

    try:
        # Verificación de seguridad
        chat = get_object_or_404(Chat, id=chat_id, users=request.user)

        total_mensajes = chat.mensaje_set.count()

        if total_mensajes == 0:
            data = {
                "mensajes": [],
                "chat_nuevo": True,
                "info": "Este es un chat nuevo. Envía el primer mensaje."
            }
        else:
            offset = max(0, total_mensajes - MENSAJES_POR_PAGINA)
            ultimos_mensajes = chat.mensaje_set.all().order_by('timestamp')[offset:]

            data = {
                "mensajes": [
                    {
                        "contenido": m.mensaje,
                        "fecha": m.timestamp.strftime("%d-%m-%Y %H:%M"),
                        "es_mio": m.user.id == request.user.id,
                        "mensaje_id": str(m.id)  # si Mensaje también usa UUID
                    } for m in ultimos_mensajes
                ],
                "chat_nuevo": False,
                "total_mensajes": total_mensajes,
                "mostrando_ultimos": len(ultimos_mensajes),
                "offset": offset
            }

        return JsonResponse(data)

    except Chat.DoesNotExist:
        return JsonResponse({"error": "Chat no encontrado o sin permisos"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno del servidor"}, status=500)


@login_required
def crear_chat(request, user_id):
    usuario = request.user
    otro_usuario = get_object_or_404(Usuario, id=user_id)

    if usuario.id == user_id:
        messages.error(request, "No puede chatear contigo mismo")
        return redirect('home')

    chat_existente = Chat.objects.filter(users=usuario).filter(users=otro_usuario).first()

    if chat_existente:
        chat = chat_existente
    else:
        chat = Chat.objects.create()
        chat.users.add(usuario, otro_usuario)
        chat.save()

    # Guardar en sesión el ID (como string para compatibilidad JSON)
    request.session['ultimo_chat_id'] = str(chat.id)

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
        except ValueError:
            print("❌ ID de chat inválido")
            return JsonResponse({'status': 'error', 'message': 'ID de chat inválido'}, status=400)
        except Chat.DoesNotExist:
            print("❌ Chat no encontrado")
            return JsonResponse({'status': 'error', 'message': 'Chat no encontrado'}, status=404)

    print("❌ Método no permitido o usuario no autenticado")
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
