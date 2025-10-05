let chatSocket = null;
let notificacionSocket = null;
let chatIdActual = null;

document.addEventListener('DOMContentLoaded', function () {

    // ==========================
    // REFERENCIAS GLOBALES
    // ==========================
    const avatar = document.getElementById('chat-avatar');
    const nombre = document.getElementById('chat-contact-name');
    const status = document.getElementById('chat-status');
    const mensajesDiv = document.getElementById('chat-messages');
    const chatContainer = document.getElementById('chat-container');
    const user = chatContainer ? chatContainer.dataset.user : null;
    const primeraChatId = chatContainer ? chatContainer.dataset.chatId : null;
    const contadorGlobal = document.getElementById('contador-conversaciones');
    const $input = $('#message-input');
    const $btn = $('#btn-enviar');

    // ==========================
    // FUNCIONES AUXILIARES
    // ==========================
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(c => {
                const cookie = c.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }

    function appendMessage(msg, esMio, datetime) {
        if (!mensajesDiv) return;
        const div = document.createElement('div');
        div.className = `d-flex mb-4 ${esMio ? 'justify-content-end' : ''}`;
        div.innerHTML = `
            <div class="flex-grow-1 me-3" style="max-width: 85%;">
                <div class="${esMio ? 'bg-primary text-white' : 'bg-light'} rounded p-3">
                    <p class="mb-1">${msg}</p>
                    <small class="text-muted">${datetime}</small>
                </div>
            </div>`;
        mensajesDiv.appendChild(div);
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }

    function marcarLeidos(chatId) {
        fetch(`/chat/marcar_leidos/${chatId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({})
        })
        .then(resp => resp.json())
        .then(() => {
            const chatElem = document.querySelector(`.conversation-item[data-id="${chatId}"]`);
            if (chatElem) {
                const badge = chatElem.querySelector('.badge');
                if (badge) badge.remove();
            }
        })
        .catch(err => console.error('❌ Error al marcar como leídos:', err));
    }

    // ==========================
    // CHAT SOCKET
    // ==========================
    function abrirWebSocket(chatId) {
        if (chatSocket) chatSocket.close();
        chatIdActual = chatId;

        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${ws_scheme}://${window.location.host}/ws/chat/${chatId}/`;
        chatSocket = new WebSocket(url);

        chatSocket.onopen = () => console.log(`💬 Conectado al chat ${chatId}`);
        chatSocket.onclose = () => console.log(`💬 Desconectado del chat ${chatId}`);

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            appendMessage(data.message, data.username === user, data.datetime);
        };
    }

    function cargarMensajes(chatId) {
        fetch(`/chat/mensajes/${chatId}/`)
            .then(resp => resp.json())
            .then(data => {
                if (!mensajesDiv) return;
                mensajesDiv.innerHTML = '';
                data.mensajes.forEach(msg => appendMessage(msg.contenido, msg.es_mio, msg.fecha));
            });
    }

    function seleccionarChat(chatId, contacto) {
        if (avatar && nombre) {
            avatar.textContent = contacto.slice(0, 2).toUpperCase();
            nombre.textContent = contacto;
        }
        if (mensajesDiv) mensajesDiv.innerHTML = '';

        abrirWebSocket(chatId);
        cargarMensajes(chatId);
        marcarLeidos(chatId);
    }

    function enviarMensaje(text) {
        if (!text || !chatSocket) return;
        appendMessage(text, true, new Date().toLocaleString());
        chatSocket.send(JSON.stringify({ message: text }));
    }

    // ==========================
    // FORMULARIO DE MENSAJES
    // ==========================
    const form = document.getElementById('message-form');
    const input = document.getElementById('message-input');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const mensaje = input.value.trim();
        if (mensaje === '') return;
        enviarMensaje(mensaje);
        input.value = '';
        input.focus();
    });

    $input.on('keypress', e => { if (e.which === 13) form.dispatchEvent(new Event('submit')); });

    $btn.on('click', () => form.dispatchEvent(new Event('submit')));

    // ==========================
    // CLICK EN CONVERSACIONES
    // ==========================
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function () {
            seleccionarChat(this.dataset.id, this.dataset.contacto);
        });
    });

    // ==========================
    // ABRIR PRIMER CHAT AUTOMÁTICAMENTE
    // ==========================
    if (primeraChatId) {
        const primerItem = document.querySelector(`.conversation-item[data-id="${primeraChatId}"]`);
        if (primerItem) primerItem.click();
    }

    function actualizarChatLista(chatId, mensaje) {
    // Panel de escritorio
    const chatElem = document.querySelector(`.conversation-item[data-id="${chatId}"]`);
    if (chatElem) {
        const ultimoMsg = chatElem.querySelector('.conversation-last-msg');
        if (ultimoMsg) ultimoMsg.textContent = mensaje;

        // Badge
        if (chatIdActual != chatId) {
            let badge = chatElem.querySelector('.badge');
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'badge bg-danger rounded-pill ms-1';
                chatElem.appendChild(badge);
            }
            badge.textContent = parseInt(badge.textContent || 0) + 1;
        } else {
            // Chat abierto, eliminar badge si existe
            const badge = chatElem.querySelector('.badge');
            if (badge) badge.remove();
        }
    }

    // Panel offcanvas
    const chatElemMobile = document.querySelector(`#lista-conversaciones-offcanvas .conversation-item[data-id="${chatId}"]`);
    if (chatElemMobile) {
        const ultimoMsg = chatElemMobile.querySelector('.conversation-last-msg');
        if (ultimoMsg) ultimoMsg.textContent = mensaje;

        if (chatIdActual != chatId) {
            let badge = chatElemMobile.querySelector('.badge');
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'badge bg-danger rounded-pill ms-1';
                chatElemMobile.appendChild(badge);
            }
            badge.textContent = parseInt(badge.textContent || 0) + 1;
        } else {
            const badge = chatElemMobile.querySelector('.badge');
            if (badge) badge.remove();
        }
    }

    // Contador global
    const contadorGlobal = document.getElementById('contador-conversaciones');
    if (contadorGlobal && chatIdActual != chatId) {
        contadorGlobal.textContent = parseInt(contadorGlobal.textContent || 0) + 1;
    }
}


    // ==========================
    // NOTIFICACIONES GLOBALES
    // ==========================
    function conectarNotificaciones() {
        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        notificacionSocket = new WebSocket(`${ws_scheme}://${window.location.host}/ws/notificaciones/`);
        console.log("🌐 Intentando conectar WebSocket de notificaciones...");

        notificacionSocket.onopen = () => console.log("🔔 WebSocket de notificaciones conectado");

        notificacionSocket.onmessage = function(e) {
    try {
        const data = JSON.parse(e.data);
        console.log("📩 Notificación recibida:", data);

        actualizarChatLista(data.chat_id, data.mensaje);

        // Si el chat está abierto, marcarlo como leído automáticamente
        if (chatIdActual == data.chat_id) {
            fetch(`/chat/marcar_leidos/${data.chat_id}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({})
            }).catch(err => console.error('❌ Error al marcar como leídos:', err));
        }
    } catch(err) {
        console.error('❌ Error procesando notificación:', err, e.data);
    }
};


        notificacionSocket.onclose = () => {
            console.warn("🔔 WebSocket de notificaciones desconectado, reintentando en 5s...");
            setTimeout(conectarNotificaciones, 5000);
        };
    }
    

    conectarNotificaciones();

    // ==========================
    // OFFCANVAS MÓVIL ≤767px
    // ==========================
    const toggleBtn = document.getElementById('toggleConversations');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            if (window.innerWidth <= 767) {
                const offcanvas = new bootstrap.Offcanvas(document.getElementById('offcanvasConversations'));
                offcanvas.show();
            }
        });
    }

});

