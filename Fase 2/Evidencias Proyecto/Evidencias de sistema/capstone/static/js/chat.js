document.addEventListener('DOMContentLoaded', function() {
    // ==========================
    // REFERENCIAS GLOBALES
    // ==========================
    const avatar = document.getElementById('chat-avatar');
    const nombre = document.getElementById('chat-contact-name');
    const status = document.getElementById('chat-status');
    const mensajesDiv = document.getElementById('chat-messages');
    const buscador = document.getElementById('buscador-conversaciones');
    const toggleBtn = document.getElementById('toggleConversations');
    const $input = $('#message-input');
    const $btn = $('#btn-enviar');

    const chatContainer = $('#chat-container');
    const user = chatContainer.data('user');

    let chatSocket = null;
    let chatIdActual = null;

    // ==========================
    // 1. BÚSQUEDA EN TIEMPO REAL
    // ==========================
    if (buscador) {
        buscador.addEventListener('input', function() {
            const busqueda = this.value.toLowerCase().trim();
            const conversaciones = document.querySelectorAll('.conversation-item');
            let visibles = 0;

            conversaciones.forEach(conv => {
                const nombreConv = conv.dataset.contacto.toLowerCase();
                const mensaje = conv.querySelector('.conversation-last-msg').textContent.toLowerCase();
                const coincide = nombreConv.includes(busqueda) || mensaje.includes(busqueda);
                if (coincide || busqueda === '') {
                    conv.classList.remove('oculta');
                    visibles++;
                } else {
                    conv.classList.add('oculta');
                }
            });

            const contador = document.getElementById('contador-conversaciones');
            if (contador) contador.textContent = visibles;
        });
    }

    // ==========================
    // 2. BOTONES RÁPIDOS
    // ==========================
    document.querySelectorAll('.quick-msg').forEach(btn => {
        btn.addEventListener('click', function() {
            const mensaje = this.dataset.msg;
            $input.val(mensaje).focus();
        });
    });

    // ==========================
    // 3. PANEL MÓVIL
    // ==========================
    let mobilePanelCreado = false;

    function cerrarPanelMovil() {
        const panel = document.getElementById('mobile-conversations');
        const overlay = document.getElementById('mobile-overlay');
        if (panel) panel.classList.remove('show');
        if (overlay) overlay.classList.remove('show');
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            let panelLateral = document.getElementById('mobile-conversations');
            let overlay = document.getElementById('mobile-overlay');

            if (!mobilePanelCreado) {
                panelLateral = document.querySelector('.col-md-5 .card').cloneNode(true);
                panelLateral.id = 'mobile-conversations';
                panelLateral.classList.add('mobile-conversations');

                const header = panelLateral.querySelector('.card-header');
                header.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="mb-0 fw-bold">💬 Conversaciones</h5>
                        <button type="button" class="btn-close" id="close-mobile-conversations"></button>
                    </div>
                `;

                document.body.appendChild(panelLateral);

                overlay = document.createElement('div');
                overlay.id = 'mobile-overlay';
                overlay.className = 'overlay';
                document.body.appendChild(overlay);

                document.getElementById('close-mobile-conversations').addEventListener('click', cerrarPanelMovil);
                overlay.addEventListener('click', cerrarPanelMovil);

                const mobileChats = panelLateral.querySelectorAll('.conversation-item');
                mobileChats.forEach(item => {
                    item.addEventListener('click', function(event) {
                        event.stopPropagation();
                        seleccionarChat(this.dataset.id, this.dataset.contacto);
                        cerrarPanelMovil();
                    });
                });

                mobilePanelCreado = true;
            }

            panelLateral.classList.add('show');
            overlay.classList.add('show');
        });
    }

    // ==========================
    // 4. FUNCIONES DE CHAT
    // ==========================
    function abrirWebSocket(chatId) {
        if(chatSocket) chatSocket.close();
        chatIdActual = chatId;

        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${ws_scheme}://${window.location.host}/ws/chat/${chatId}/`;

        chatSocket = new WebSocket(url);
        console.log('Conectando WebSocket a:', url);

        chatSocket.onopen = () => console.log('WEBSOCKET ABIERTO');
        chatSocket.onclose = () => console.log('WEBSOCKET CERRADO');

        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);

            // Determinar si el mensaje es tuyo
            const esMio = data.username === user;

            const msgHTML = `
                <div class="d-flex mb-4 ${esMio ? 'justify-content-end' : ''}">
                    <div class="flex-grow-1 me-3" style="max-width: 85%;">
                        <div class="${esMio ? 'bg-primary text-white' : 'bg-light'} rounded p-3">
                            <p class="mb-1">${data.message}</p>
                            <small class="text-muted">${data.datetime}</small>
                        </div>
                    </div>
                </div>
            `;

            $('#chat-messages').append(msgHTML);
            $('#chat-messages')[0].scrollTop = $('#chat-messages')[0].scrollHeight;
        };
    }

    function sendMessage() {
        const text = $input.val().trim();
        if (!text || !chatSocket) return;

        // Mostrar mensaje local
        const localHTML = `
        <div class="d-flex mb-4 justify-content-end">
            <div class="flex-grow-1 me-3" style="max-width: 85%;">
                <div class="bg-primary text-white rounded p-3">
                    <p class="mb-1">${text}</p>
                    <small class="text-muted">${new Date().toLocaleString()}</small>
                </div>
            </div>
        </div>`;
        $('#chat-messages').append(localHTML);
        $('#chat-messages')[0].scrollTop = $('#chat-messages')[0].scrollHeight;

        // Enviar al WebSocket
        chatSocket.send(JSON.stringify({ message: text }));
        $input.val('');
    }
    $btn.on('click', sendMessage);
    $input.on('keypress', function(e) {
        if(e.which === 13) sendMessage();
    });

    function cargarMensajes(chatId) {
        fetch(`/chat/mensajes/${chatId}/`)
        .then(resp => resp.json())
        .then(data => {
            if (!mensajesDiv) return;
            mensajesDiv.innerHTML = '';

            data.mensajes.forEach(msg => {
                const div = document.createElement('div');
                div.className = msg.es_mio ? 'd-flex mb-4 justify-content-end' : 'd-flex mb-4';
                div.innerHTML = `
                    <div class="flex-grow-1 me-3" style="max-width: 85%;">
                        <div class="${msg.es_mio ? 'bg-primary text-white' : 'bg-light'} rounded p-3">
                            <p class="mb-1">${msg.contenido}</p>
                            <small class="text-muted">${msg.fecha}</small>
                        </div>
                    </div>`;
                mensajesDiv.appendChild(div);
            });

            mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
        })
        .catch(err => console.error('Error al cargar mensajes:', err));
    }

    function seleccionarChat(chatId, contacto) {
        if (avatar && nombre && status) {
            avatar.textContent = contacto.slice(0,2).toUpperCase();
            nombre.textContent = contacto;
        }

        if (mensajesDiv) mensajesDiv.innerHTML = '';

        abrirWebSocket(chatId);
        cargarMensajes(chatId);
    }

    // ==========================
    // 5. ASIGNAR CLICK A CONVERSACIONES (desktop)
    // ==========================
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function() {
            seleccionarChat(this.dataset.id, this.dataset.contacto);
        });
    });

    // ==========================
    // 6. CARGAR PRIMERA CONVERSACIÓN AUTOMÁTICAMENTE
    // ==========================
    const conversaciones = document.querySelectorAll('.conversation-item');
    if (conversaciones.length > 0) conversaciones[0].click();
});
