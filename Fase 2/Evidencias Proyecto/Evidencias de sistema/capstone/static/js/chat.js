document.addEventListener('DOMContentLoaded', function () {
    const chatContainer = document.getElementById('chat-container');
    const userId = chatContainer ? chatContainer.dataset.user : null;
    let chatId = chatContainer ? chatContainer.dataset.chatId : null;

    const chatMessagesDiv = document.getElementById('chat-messages');
    const input = document.getElementById('message-input');
    const btn = document.getElementById('btn-enviar');
    const chatNombreHeader = document.getElementById('chat-nombre');

    const offcanvasConversaciones = document.getElementById('offcanvasConversaciones');
    const offcanvasInstance = offcanvasConversaciones ? bootstrap.Offcanvas.getOrCreateInstance(offcanvasConversaciones) : null;

    let chatSocket = null; // WebSocket global

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function appendMessage(msg, esMio, datetime) {
        if (!chatMessagesDiv) return;

        const div = document.createElement('div');
        div.className = `d-flex mb-3 ${esMio ? 'justify-content-end' : 'justify-content-start'}`;

        // Estilos del globo del mensaje
        const bubbleStyle = `
        display: inline-block;
        padding: 12px 16px;
        border-radius: 18px;
        max-width: 70%;
        word-wrap: break-word;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ${esMio ?
                'background: linear-gradient(135deg, #0d6efd, #0b5ed7); color: white; border-bottom-right-radius: 4px;' :
                'background-color: #f8f9fa; color: #212529; border: 1px solid #e9ecef; border-bottom-left-radius: 4px;'
            }
        position: relative;
    `;

        const timeStyle = `
        display: block;
        font-size: 0.7rem;
        margin-top: 6px;
        text-align: ${esMio ? 'right' : 'left'};
        color: ${esMio ? 'rgba(255,255,255,0.7)' : '#6c757d'};
        font-weight: 400;
    `;

        div.innerHTML = `
        <div style="${bubbleStyle}">
            <p class="mb-0" style="line-height: 1.4; font-size: 0.95rem;">${msg}</p>
            <small style="${timeStyle}">${datetime}</small>
        </div>
    `;

        chatMessagesDiv.appendChild(div);
        chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
    }


    async function cargarMensajes(id) {
        if (!id) return;
        try {
            const res = await fetch(`/chat/mensajes/${id}/`);
            const data = await res.json();
            chatMessagesDiv.innerHTML = '';
            data.mensajes.forEach(m => appendMessage(m.contenido, m.es_mio, m.fecha));
            if (data.mensajes.some(m => !m.es_mio && !m.leido))
                console.log("Mensajes marcados leidos")
            marcarMensajesLeidos(id);
        } catch (err) {
            console.error('❌ Error cargando mensajes:', err);
        }
    }

    async function marcarMensajesLeidos(id) {
        try {
            const res = await fetch(`/chat/marcar_leidos/${id}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });
            const data = await res.json();
            if (data.status === 'ok') {
                const badge = document.getElementById(`badge-${id}`);
                if (badge) badge.remove();
            }
        } catch (err) {
            console.error('❌ Error fetch marcar_leidos:', err);
        }
    }

    function abrirWebSocket(id) {
        // Si ya hay un WebSocket abierto, cerrarlo primero
        if (chatSocket && chatSocket.readyState !== WebSocket.CLOSED) {
            console.log(`🔌 Cerrando WebSocket anterior...`);
            try {
                chatSocket.close();
            } catch (e) {
                console.error("⚠️ Error al cerrar WebSocket anterior:", e);
            }
            chatSocket = null;
        }

        const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
        const wsUrl = `${wsScheme}://${window.location.host}/ws/chat/${id}/`;

        console.log(`🔗 Conectando WebSocket al chat ${id}...`);
        chatSocket = new WebSocket(wsUrl);

        chatSocket.onopen = function () {
            console.log(`✅ WebSocket conectado correctamente al chat ${id}`);
        };

        chatSocket.onmessage = function (e) {
            try {
                const data = JSON.parse(e.data);
                appendMessage(data.message, data.user_id == userId, data.timestamp);
            } catch (err) {
                console.error("⚠️ Error al procesar mensaje recibido:", err);
            }
        };

        chatSocket.onclose = function (e) {
            console.log(`❌ WebSocket cerrado (${id})`, e);
            chatSocket = null;
        };

        chatSocket.onerror = function (err) {
            console.error("🚨 Error en WebSocket:", err);
        };
    }

    function seleccionarChat(element) {
        chatId = element.dataset.id;
        chatNombreHeader.textContent = element.dataset.contacto;

        document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
        element.classList.add('active');

        chatMessagesDiv.innerHTML = `<div class="h-100 d-flex flex-column align-items-center justify-content-center text-center text-muted">
            <div class="mb-3"><i class="bi bi-chat-dots display-4"></i></div>
            <h5>Cargando conversación...</h5>
        </div>`;

        if (offcanvasInstance) offcanvasInstance.hide();

        cargarMensajes(chatId);
        abrirWebSocket(chatId); // Abrir WebSocket para este chat
    }

    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function () {
            seleccionarChat(this);
        });
    });

    function enviarMensaje(text) {
        if (!text || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;
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
    } else {
        console.warn('⚠️ No se encontraron elementos del input o botón de enviar.');
    }

    // Cargar primer chat y abrir su WebSocket
    if (chatId) {
        cargarMensajes(chatId);
        abrirWebSocket(chatId);
    }
});
