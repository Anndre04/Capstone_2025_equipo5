// static/js/chat.js
let chatSocket = null;
let chatIdActual = null;

document.addEventListener('DOMContentLoaded', function () {
    // ==========================
    // REFERENCIAS GLOBALES
    // ==========================
    const avatar = document.getElementById('chat-avatar');
    const nombre = document.getElementById('chat-contact-name');
    const mensajesDiv = document.getElementById('chat-messages');
    const chatContainer = document.getElementById('chat-container');
    const user = chatContainer ? chatContainer.dataset.user : null;
    const primeraChatId = chatContainer ? chatContainer.dataset.chatId : null;
    const $input = $('#message-input');
    const $btn = $('#btn-enviar');
    const form = document.getElementById('message-form');
    const input = document.getElementById('message-input');

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

    function actualizarPlaceholderInput(esChatNuevo) {
        if (input) {
            input.placeholder = esChatNuevo ? 
                "Escribe el primer mensaje..." : 
                "Escribe tu mensaje...";
        }
    }

    // ==========================
    // CARGAR MENSAJES
    // ==========================
    function cargarMensajes(chatId) {
        fetch(`/chat/mensajes/${chatId}/`)
            .then(resp => {
                if (!resp.ok) throw new Error(`Error: ${resp.status}`);
                return resp.json();
            })
            .then(data => {
                if (!mensajesDiv) return;
                
                mensajesDiv.innerHTML = '';
                
                if (data.chat_nuevo) {
                    const div = document.createElement('div');
                    div.className = 'text-center text-muted py-5';
                    div.innerHTML = `
                        <div class="mb-3">
                            <i class="bi bi-chat-dots display-4"></i>
                        </div>
                        <h5>¡Comienza la conversación!</h5>
                        <p class="mb-0">${data.info || 'Envía el primer mensaje'}</p>
                    `;
                    mensajesDiv.appendChild(div);
                } else if (data.mensajes && data.mensajes.length > 0) {
                    data.mensajes.forEach(msg => {
                        appendMessage(msg.contenido, msg.es_mio, msg.fecha);
                    });

                    if (data.total_mensajes > data.mostrando_ultimos) {
                        const mensajesFaltantes = data.total_mensajes - data.mostrando_ultimos;
                        const div = document.createElement('div');
                        div.className = 'text-center text-muted py-2';
                        div.innerHTML = `<small>... ${mensajesFaltantes} mensajes anteriores</small>`;
                        mensajesDiv.insertBefore(div, mensajesDiv.firstChild);
                    }
                } else {
                    const div = document.createElement('div');
                    div.className = 'text-center text-muted py-5';
                    div.innerHTML = `
                        <div class="mb-3">
                            <i class="bi bi-chat-x display-4"></i>
                        </div>
                        <p>No hay mensajes en esta conversación</p>
                    `;
                    mensajesDiv.appendChild(div);
                }
                
                actualizarPlaceholderInput(data.chat_nuevo);
            })
            .catch(err => {
                if (mensajesDiv) {
                    mensajesDiv.innerHTML = `
                        <div class="alert alert-danger text-center">
                            <i class="bi bi-exclamation-triangle"></i>
                            <p class="mb-0">Error al cargar los mensajes</p>
                        </div>
                    `;
                }
            });
    }

    // ==========================
    // MARCAR MENSAJES COMO LEÍDOS
    // ==========================
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
            const elementos = document.querySelectorAll(`.conversation-item[data-id="${chatId}"]`);
            elementos.forEach(elem => {
                const badge = elem.querySelector('.badge');
                if (badge) badge.remove();
            });
        })
        .catch(err => console.error('Error al marcar como leídos:', err));
    }

    // ==========================
    // WEBSOCKET DEL CHAT
    // ==========================
    function abrirWebSocket(chatId) {
        if (chatSocket) chatSocket.close();
        chatIdActual = chatId;

        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${ws_scheme}://${window.location.host}/ws/chat/${chatId}/`;
        chatSocket = new WebSocket(url);

        chatSocket.onopen = () => console.log(`Conectado al chat ${chatId}`);
        chatSocket.onclose = () => console.log(`Desconectado del chat ${chatId}`);

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            appendMessage(data.message, data.username === user, data.datetime);
        };
    }

    // ==========================
    // SELECCIONAR CHAT
    // ==========================
    function seleccionarChat(chatId, contacto) {
        if (avatar && nombre) {
            avatar.textContent = contacto.slice(0, 2).toUpperCase();
            nombre.textContent = contacto;
        }

        abrirWebSocket(chatId);
        cargarMensajes(chatId);
        marcarLeidos(chatId);

        if (window.innerWidth <= 767) {
            const offcanvasEl = document.getElementById('offcanvasConversaciones');
            const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl) || new bootstrap.Offcanvas(offcanvasEl);
            bsOffcanvas.hide();
        }
    }

    // ==========================
    // ENVIAR MENSAJE
    // ==========================
    function enviarMensaje(text) {
        if (!text || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;
        appendMessage(text, true, new Date().toLocaleString());
        chatSocket.send(JSON.stringify({ message: text }));
    }

    // ==========================
    // MANEJO DEL FORMULARIO
    // ==========================
    function manejarEnvioMensaje(e) {
        if (e) e.preventDefault();
        
        const mensaje = input.value.trim();
        if (mensaje === '' || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;

        enviarMensaje(mensaje);
        input.value = '';
        input.focus();
    }

    if (form && input) {
        form.addEventListener('submit', manejarEnvioMensaje);
    }

    $input.on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            manejarEnvioMensaje(e);
        }
    });

    $btn.on('click', function(e) {
        e.preventDefault();
        manejarEnvioMensaje(e);
    });

    // ==========================
    // EVENTOS DE CONVERSACIONES
    // ==========================
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function () {
            const chatId = this.dataset.id;
            const contacto = this.dataset.contacto;
            seleccionarChat(chatId, contacto);
        });
    });

    // ==========================
    // INICIALIZAR PRIMER CHAT
    // ==========================
    function inicializarPrimerChat() {
        if (primeraChatId) {
            const primerItem = document.querySelector(`.conversation-item[data-id="${primeraChatId}"]`);
            if (primerItem) {
                const contacto = primerItem.dataset.contacto;
                seleccionarChat(primeraChatId, contacto);
            } else {
                seleccionarChat(primeraChatId, 'Contacto');
            }
        }
    }

    inicializarPrimerChat();

    // ==========================
    // ACTUALIZAR LISTA DE CHATS
    // ==========================
    function actualizarChatLista(chatId, mensaje) {
        const elementos = document.querySelectorAll(`.conversation-item[data-id="${chatId}"]`);
        const esChatActual = chatIdActual === chatId;

        elementos.forEach(chatElem => {
            const ultimoMsg = chatElem.querySelector('.conversation-last-msg, .small');
            if (ultimoMsg) ultimoMsg.textContent = mensaje;

            if (!esChatActual) {
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

            const lista = chatElem.closest('#lista-conversaciones, #lista-conversaciones-movil');
            if (lista) lista.prepend(chatElem);
        });
    }

    // ==========================
    // OFFCANVAS MÓVIL
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

    // ==========================
    // FUNCIÓN PARA NOTIFICACIONES
    // ==========================
    window.manejarNotificacionMensaje = function(notificacion) {
        const chatId = notificacion.datos_extra?.chat_id;
        const mensaje = notificacion.mensaje;
        
        if (!chatId) return;

        // Actualizar lista de chats
        actualizarChatLista(chatId, mensaje);

        // Si el chat está abierto, marcar como leído
        if (chatIdActual == chatId) {
            fetch(`/chat/marcar_leidos/${chatId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            }).catch(err => console.error('Error al marcar como leídos:', err));
            
            // Mostrar mensaje en chat activo si es de otro usuario
            const senderId = notificacion.datos_extra?.sender_id;
            if (senderId && chatContainer) {
                const currentUserId = chatContainer.dataset.user;
                if (senderId != currentUserId) {
                    appendMessage(mensaje, false, new Date().toLocaleString());
                }
            }
        }
    };
});