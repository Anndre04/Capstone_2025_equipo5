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


        // ==========================
        // MARCAR MENSAJES COMO LEÍDOS EN BACKEND
        // ==========================
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
                // ==========================
                // ELIMINAR BADGE DEL CHAT ABIERTO
                // ==========================
                const chatElemDesktop = document.querySelector(`.conversation-item[data-id="${chatId}"]`);
                if (chatElemDesktop) {
                    const badge = chatElemDesktop.querySelector('.badge');
                    if (badge) badge.remove();
                }

                const chatElemMobile = document.querySelector(`#lista-conversaciones-movil .conversation-item[data-id="${chatId}"]`);
                if (chatElemMobile) {
                    const badge = chatElemMobile.querySelector('.badge');
                    if (badge) badge.remove();
                }

                // ==========================
                // ACTUALIZAR CONTADOR GLOBAL
                // ==========================
                const contadorGlobal = document.getElementById('contador-conversaciones');
                if (contadorGlobal) {
                    let total = 0;
                    document.querySelectorAll('.conversation-item .badge').forEach(b => {
                        total += parseInt(b.textContent || 0);
                    });
                    contadorGlobal.textContent = total;
                    if (total === 0) contadorGlobal.classList.add('d-none');
                }
            })
            .catch(err => console.error('❌ Error al marcar como leídos:', err));
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

    form.addEventListener('submit', function (e) {
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
            const chatId = this.dataset.id;
            const contacto = this.dataset.contacto;

            // Selecciona el chat
            seleccionarChat(chatId, contacto);

            // Si estamos en móvil y el chat está en el offcanvas, cerrarlo
            if (window.innerWidth <= 767) {
                const offcanvasEl = document.getElementById('offcanvasConversaciones');
                const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl)
                    || new bootstrap.Offcanvas(offcanvasEl);
                bsOffcanvas.hide();
            }
        });
    });

    // ==========================
    // ABRIR PRIMER CHAT AUTOMÁTICAMENTE
    // ==========================
    if (primeraChatId) {
        const primerItem = document.querySelector(`.conversation-item[data-id="${primeraChatId}"]`);
        if (primerItem) primerItem.click();
    }

    // ==========================
    // ACTUALIZAR LISTA DE CHATS (Desktop y Móvil)
    // ==========================
    function actualizarChatLista(chatId, mensaje) {
        console.log("🧩 Actualizando chat:", chatId);

        // === PANEL DE ESCRITORIO ===
        const listaDesktop = document.getElementById('lista-conversaciones');
        if (listaDesktop) {
            const chatElem = listaDesktop.querySelector(`.conversation-item[data-id="${chatId}"]`);
            if (chatElem) {
                console.log("💻 Chat encontrado en panel de escritorio:", chatElem);

                // Actualiza último mensaje
                const ultimoMsg = chatElem.querySelector('.conversation-last-msg');
                if (ultimoMsg) ultimoMsg.textContent = mensaje;

                // Si el chat no está activo, muestra o incrementa badge
                if (chatIdActual != chatId) {
                    let badge = chatElem.querySelector('.badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'badge bg-danger rounded-pill position-absolute end-0 me-3';
                        badge.textContent = "1";
                        chatElem.appendChild(badge);
                    } else {
                        badge.textContent = parseInt(badge.textContent || 0) + 1;
                    }
                } else {
                    const badge = chatElem.querySelector('.badge');
                    if (badge) badge.remove();
                }

                // Mover chat al inicio de la lista
                listaDesktop.prepend(chatElem);
            } else {
                console.warn("⚠️ No se encontró chat en escritorio con id:", chatId);
            }
        }

        // === PANEL OFFCANVAS (MÓVIL) ===
        const listaMovil = document.getElementById('lista-conversaciones-movil');
        if (listaMovil) {
            const chatElemMobile = listaMovil.querySelector(`.conversation-item[data-id="${chatId}"]`);
            if (chatElemMobile) {
                const ultimoMsg = chatElemMobile.querySelector('.small');
                if (ultimoMsg) ultimoMsg.textContent = mensaje;

                if (chatIdActual != chatId) {
                    let badge = chatElemMobile.querySelector('.badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'badge bg-danger rounded-pill position-absolute end-0 me-3';
                        badge.textContent = "1";
                        chatElemMobile.appendChild(badge);
                    } else {
                        badge.textContent = parseInt(badge.textContent || 0) + 1;
                    }
                } else {
                    const badge = chatElemMobile.querySelector('.badge');
                    if (badge) badge.remove();
                }

                // Mover chat al inicio de la lista móvil
                listaMovil.prepend(chatElemMobile);
            }
        }

        // === CONTADOR GLOBAL (si existe) ===
        const contadorGlobal = document.getElementById('contador-conversaciones');
        if (contadorGlobal && chatIdActual != chatId) {
            contadorGlobal.textContent = parseInt(contadorGlobal.textContent || 0) + 1;
            contadorGlobal.classList.remove('d-none');
        }
    }

    // ==========================
    // WEBSOCKET DE NOTIFICACIONES
    // ==========================
    function conectarNotificaciones() {
        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const notificacionSocket = new WebSocket(`${ws_scheme}://${window.location.host}/ws/notificaciones/`);
        console.log("🌐 Conectando WebSocket de notificaciones...");

        notificacionSocket.onopen = () => console.log("🔔 WebSocket conectado");

        notificacionSocket.onmessage = function (e) {
            try {
                const data = JSON.parse(e.data);
                console.log("📩 Notificación recibida:", data);

                actualizarChatLista(data.chat_id, data.mensaje);

                if (chatIdActual == data.chat_id) {
                    fetch(`/chat/marcar_leidos/${data.chat_id}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    }).catch(err => console.error('❌ Error al marcar como leídos:', err));
                }
            } catch (err) {
                console.error('❌ Error procesando notificación:', err, e.data);
            }
        };

        notificacionSocket.onclose = () => {
            console.warn("🔔 WebSocket desconectado, reintentando en 5s...");
            setTimeout(conectarNotificaciones, 5000);
        };
    }

    conectarNotificaciones();
    
    // ==========================
    // OFFCANVAS MÓVIL (≤767px)
    // ==========================
    const toggleBtn = document.getElementById('toggleConversations');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            if (window.innerWidth <= 767) {
                const offcanvas = new bootstrap.Offcanvas(document.getElementById('offcanvasConversaciones'));
                offcanvas.show();
            }
        });
    }
});

