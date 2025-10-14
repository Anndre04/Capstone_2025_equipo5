let notiSocket;


// --------------------
// Inicialización al cargar la página
// --------------------
document.addEventListener("DOMContentLoaded", () => {
    conectarNotificaciones();
    cargarNotificacionesDropdown();

    // --------------------
    // Obtener Cookie
    // --------------------

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // ¿Esta cookie comienza con el nombre buscado?
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --------------------
    // Conexión al WebSocket de notificaciones
    // --------------------
    function conectarNotificaciones() {
        const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
        notiSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/notificaciones/`);

        notiSocket.onopen = () => {
            console.log("✅ Conectado al WebSocket de notificaciones");
        };

        notiSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            console.log("🔔 Notificación recibida:", data);
            agregarNotificacionAlDropdown(data); // Agrega la notificación en el dropdown
            actualizarBadge();
        };

        notiSocket.onclose = (e) => {
            console.log("❌ WebSocket de notificaciones cerrado", e);
        };

        notiSocket.onerror = (err) => {
            console.error("❌ Error WebSocket de notificaciones", err);
        };
    }

    // --------------------
    // Actualiza el badge con el conteo de no leídas
    // --------------------
    function actualizarBadge() {
        fetch("/notificaciones/no-leidas/")
            .then(response => response.json())
            .then(data => {
                const badge = document.getElementById("notification-count");
                badge.textContent = data.count;
            })
            .catch(err => console.error("Error actualizando badge:", err));
    }

    // --------------------
    // Carga las notificaciones en el dropdown
    // --------------------
    function cargarNotificacionesDropdown() {
        fetch("/notificaciones/lista/")
            .then(response => response.json())
            .then(data => {
                const list = document.getElementById("notifications-list");
                list.innerHTML = ""; // Limpiar contenido

                if (data.notificaciones.length === 0) {
                    list.innerHTML = `
                    <div class="text-center py-3 text-muted">
                        <i class="bi bi-bell-slash display-6"></i>
                        <p class="mb-0 small">No hay notificaciones</p>
                    </div>`;
                    return;
                }

                data.notificaciones.forEach(n => {
                    const leidaClass = n.leida ? "text-muted" : "fw-bold";
                    const item = document.createElement("li");
                    item.className = `dropdown-item ${leidaClass}`;
                    item.innerHTML = `
                        <div style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word;">
                            <i class="${n.icono} text-${n.color} me-2"></i>
                            <strong>${n.titulo}</strong>
                            <p class="mb-0 small" style="
                                max-height: 40px;      /* altura máxima del mensaje */
                                overflow: hidden;       /* oculta el exceso */
                                text-overflow: ellipsis; /* agrega ... */
                                display: -webkit-box;
                                -webkit-line-clamp: 1;   /* máximo 2 líneas */
                                -webkit-box-orient: vertical;
                            ">
                                ${n.mensaje}
                            </p>
                        </div>
                    `;



                    // Click para marcar como leída
                    item.addEventListener("click", () => {
                        marcarNotificacionLeida(n.id, item);
                    });

                    list.appendChild(item);
                });
            })
            .catch(err => console.error("Error cargando notificaciones:", err));
    }

    // --------------------
    // Agrega una notificación al dropdown dinámicamente
    // --------------------
    function agregarNotificacionAlDropdown(n) {
        const list = document.getElementById("notifications-list");
        const item = document.createElement("li");
        item.className = "dropdown-item fw-bold"; // Nueva notificación
        item.innerHTML = `
            <i class="${n.icono} text-${n.color} me-2"></i>
            ${n.titulo} - <small>${n.mensaje}</small>`;

        item.addEventListener("click", () => {
            marcarNotificacionLeida(n.id, item);

            if (n.datos_extra && n.datos_extra.url) {
                // Redirigir a la URL de la notificación
                window.location.href = `/${n.datos_extra.url}`;
            }
        });

        // Insertar al inicio
        list.prepend(item);
        actualizarBadge();
    }


    // --------------------
    // Marca una notificación como leída
    // --------------------
    function marcarNotificacionLeida(id, elemento) {
        fetch(`/notificaciones/${id}/marcar-leida/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    elemento.classList.remove("fw-bold");
                    elemento.classList.add("text-muted");
                    actualizarBadge();
                }
            })
            .catch(err => console.error("Error marcando notificación:", err));
    }

    // --------------------
    // Marca todas las notificaciones como leídas
    // --------------------
    function marcarTodasNotificaciones() {
        fetch("/notificaciones/marcar-todas-leidas/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken") // Función que obtiene el CSRF token
            },
            body: JSON.stringify({})
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log("✅ Todas las notificaciones marcadas como leídas");
                    actualizarBadge(); // actualizar badge
                } else {
                    console.error("❌ Error marcando todas las notificaciones:", data.error);
                }
            })
            .catch(err => console.error("❌ Error en fetch:", err));
    }



    // Botón "Marcar todas"
    const btnMarcarTodas = document.getElementById("mark-all-read");
    if (btnMarcarTodas) {
        btnMarcarTodas.addEventListener("click", () => {
            marcarTodasNotificaciones();
        });
    }
});
