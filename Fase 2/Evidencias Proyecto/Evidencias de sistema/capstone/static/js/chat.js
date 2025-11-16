/** CHAT GENERAL — MÓDULO INDEPENDIENTE
 * 100% aislado del WebRTC y videollamada.js
 * Puede convivir sin conflictos en la misma página
 * Incluye hook global opcional para abrir chat desde fuera
 */
document.addEventListener('DOMContentLoaded', function () {

    // Si no existe el contenedor, no iniciar el chat
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) {
        console.warn("💬 Chat general: no hay contenedor, módulo inactivo");
        return;
    }

    // Datos base del chat
    const userId = chatContainer.dataset.user || null;
    let chatId = chatContainer.dataset.chatId || null;

    // Elementos
    const chatMessagesDiv = document.getElementById('chat-messages');
    const input = document.getElementById('message-input');
    const btn = document.getElementById('btn-enviar');
    const chatNombreHeader = document.getElementById('chat-nombre');

    const offcanvasConversaciones = document.getElementById('offcanvasConversaciones');
    const offcanvasInstance = offcanvasConversaciones ? bootstrap.Offcanvas.getOrCreateInstance(offcanvasConversaciones) : null;

    let chatSocket = null;


    // ---- UTILS ---- //

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


    // ---- UI ---- //

    function appendMessage(msg, esMio, datetime) {
        if (!chatMessagesDiv) return;

        const div = document.createElement('div');
        div.className = `d-flex mb-3 ${esMio ? 'justify-content-end' : 'justify-content-start'}`;

        div.innerHTML = `
            <div style="
                display:inline-block;padding:12px 16px;border-radius:18px;max-width:70%;
                box-shadow:0 1px 3px rgba(0,0,0,0.1);word-wrap:break-word;
                ${esMio ?
                    'background:linear-gradient(135deg,#0d6efd,#0b5ed7);color:white;border-bottom-right-radius:4px;' :
                    'background-color:#f8f9fa;color:#212529;border:1px solid #e9ecef;border-bottom-left-radius:4px;'
                }
            ">
                <p class="mb-0" style="line-height:1.4;font-size:0.95rem;">${msg}</p>
                <small style="
                    display:block;font-size:0.7rem;margin-top:6px;
                    text-align:${esMio ? 'right' : 'left'};
                    color:${esMio ? 'rgba(255,255,255,0.7)' : '#6c757d'};
                ">
                    ${datetime}
                </small>
            </div>
        `;

        chatMessagesDiv.appendChild(div);
        chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
    }


    // ---- FETCH ---- //

    async function cargarMensajes(id) {
        try {
            const res = await fetch(`/chat/mensajes/${id}/`);
            const data = await res.json();

            chatMessagesDiv.innerHTML = '';

            data.mensajes.forEach(m =>
                appendMessage(m.contenido, m.es_mio, m.fecha)
            );

            if (data.mensajes.some(m => !m.es_mio && !m.leido))
                marcarMensajesLeidos(id);

        } catch (err) {
            console.error('❌ Error cargando mensajes:', err);
        }
    }

    async function marcarMensajesLeidos(id) {
        try {
            const res = await fetch(`/chat/marcar_leidos/${id}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            const data = await res.json();

            if (data.status === 'ok') {
                const badge = document.getElementById(`badge-${id}`);
                if (badge) badge.remove();
            }

        } catch (err) {
            console.error('❌ Error marcar_leidos:', err);
        }
    }


    // ---- WEBSOCKET ---- //

    function abrirWebSocket(id) {

        if (chatSocket && chatSocket.readyState !== WebSocket.CLOSED) {
            try { chatSocket.close(); } catch { }
        }

        const wsScheme = location.protocol === "https:" ? "wss" : "ws";
        chatSocket = new WebSocket(`${wsScheme}://${location.host}/ws/chat/${id}/`);

        chatSocket.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                appendMessage(data.message, data.user_id == userId, data.timestamp);
            } catch { }
        };

        chatSocket.onclose = () => {
            chatSocket = null;
            console.log("💬 WS cerrado");
        };
    }


    // ---- SELECCIÓN DE CHAT ---- //

    function seleccionarChat(element) {
        chatId = element.dataset.id;
        chatNombreHeader.textContent = element.dataset.contacto;

        document.querySelectorAll('.conversation-item')
            .forEach(el => el.classList.remove('active'));

        element.classList.add('active');

        chatMessagesDiv.innerHTML = `
            <div class="h-100 d-flex flex-column align-items-center justify-content-center text-center text-muted">
                <div class="mb-3"><i class="bi bi-chat-dots display-4"></i></div>
                <h5>Cargando conversación...</h5>
            </div>
        `;

        if (offcanvasInstance) offcanvasInstance.hide();

        cargarMensajes(chatId);
        abrirWebSocket(chatId);
    }


    // Click en los items
    document.querySelectorAll('.conversation-item')
        .forEach(item =>
            item.addEventListener('click', () => seleccionarChat(item))
        );


    // ---- ENVIAR ---- //

    function enviarMensaje(text) {
        if (!text || !chatSocket || chatSocket.readyState !== WebSocket.OPEN)
            return;

        chatSocket.send(JSON.stringify({ message: text }));
        input.value = '';
        input.focus();
    }

    if (btn && input) {
        btn.addEventListener('click', () => enviarMensaje(input.value.trim()));
        input.addEventListener('keypress', e => {
            if (e.key === 'Enter') {
                e.preventDefault();
                enviarMensaje(input.value.trim());
            }
        });
    }


    // ---- AUTO LOAD ---- //

    if (chatId) {
        cargarMensajes(chatId);
        abrirWebSocket(chatId);
    }


    // HOOK PÚBLICO PARA VIDEOLLAMADA, SI LO NECESITAS ALGÚN DÍA
    window.ChatModule = {
        openChat: seleccionarChat,
        send: enviarMensaje
    };

});
