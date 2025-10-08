// static/js/notifications.js

class NotificationManager {
    constructor() {
        this.notificationSocket = null;
        this.isConnected = false;
        this.init();
    }

    init() {
        this.conectarWebSocket();
        this.setupEventListeners();
        this.cargarContadorInicial();
    }

    // ==========================
    // WEBSOCKET - CONEXIÓN
    // ==========================
    conectarWebSocket() {
        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        this.notificationSocket = new WebSocket(`${ws_scheme}://${window.location.host}/ws/notificaciones/`);

        this.notificationSocket.onopen = () => {
            console.log("🔔 WebSocket de notificaciones conectado");
            this.isConnected = true;
            this.cargarContadorNotificaciones();
        };

        this.notificationSocket.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                this.manejarMensajeWebSocket(data);
            } catch (err) {
                console.error('❌ Error procesando mensaje WebSocket:', err);
            }
        };

        this.notificationSocket.onclose = () => {
            console.warn("🔔 WebSocket desconectado, reintentando en 5s...");
            this.isConnected = false;
            setTimeout(() => this.conectarWebSocket(), 5000);
        };

        this.notificationSocket.onerror = (error) => {
            console.error('❌ Error en WebSocket:', error);
        };
    }

    // ==========================
    // MANEJAR MENSAJES WEBSOCKET
    // ==========================
    manejarMensajeWebSocket(data) {
        if (data.type === "notificacion") {
            this.manejarNotificacionGlobal(data);
        }
    }

    // ==========================
    // EVENT LISTENERS
    // ==========================
    setupEventListeners() {
        // Dropdown show event
        const dropdown = document.getElementById('notificationsDropdown');
        if (dropdown) {
            dropdown.addEventListener('show.bs.dropdown', () => {
                this.cargarNotificacionesDropdown();
            });
        }

        // Marcar todas como leídas
        const markAllBtn = document.getElementById('mark-all-read');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.marcarTodasComoLeidas();
            });
        }
    }

    // ==========================
    // CARGAR CONTADOR INICIAL
    // ==========================
    cargarContadorInicial() {
        this.cargarContadorNotificaciones();
    }

    // ==========================
    // CONTADOR DE NOTIFICACIONES
    // ==========================
    cargarContadorNotificaciones() {
        fetch('/notificaciones/no-leidas/')
            .then(resp => resp.json())
            .then(data => {
                this.actualizarBadgeNotificaciones(data.count);
            })
            .catch(err => console.error('❌ Error cargando contador:', err));
    }

    actualizarBadgeNotificaciones(count) {
        const badge = document.getElementById('notification-count');
        if (badge) {
            badge.textContent = count;
            if (count > 0) {
                badge.style.display = 'block';
                badge.classList.add('pulse-animation');
            } else {
                badge.style.display = 'none';
                badge.classList.remove('pulse-animation');
            }
        }
    }

    // ==========================
    // DROPDOWN DE NOTIFICACIONES
    // ==========================
    cargarNotificacionesDropdown() {
        fetch('/notificaciones/lista/')
            .then(resp => resp.json())
            .then(data => {
                this.renderizarNotificacionesDropdown(data.notificaciones);
                this.actualizarBadgeNotificaciones(data.total_no_leidas);
            })
            .catch(err => console.error('❌ Error cargando notificaciones:', err));
    }

    renderizarNotificacionesDropdown(notificaciones) {
        const container = document.getElementById('notifications-list');
        
        if (!notificaciones || notificaciones.length === 0) {
            container.innerHTML = this.getEmptyStateHTML();
            return;
        }

        let html = '';
        notificaciones.forEach(notif => {
            html += this.getNotificationItemHTML(notif);
        });
        
        container.innerHTML = html;
        this.setupNotificationItemListeners();
    }

    getEmptyStateHTML() {
        return `
            <div class="text-center py-3 text-muted">
                <i class="bi bi-bell-slash display-6"></i>
                <p class="mb-0 small">No hay notificaciones</p>
            </div>
        `;
    }

    getNotificationItemHTML(notif) {
        const timeAgo = this.calcularTiempoTranscurrido(notif.fecha_creacion);
        const unreadClass = notif.leida ? '' : 'unread';
        const newBadge = !notif.leida ? '<div class="ms-2"><span class="badge bg-primary rounded-pill">Nuevo</span></div>' : '';
        
        return `
            <li class="notification-item ${unreadClass}" data-id="${notif.id}">
                <div class="d-flex align-items-start p-2">
                    <div class="notification-icon bg-${notif.color} text-white me-2">
                        <i class="bi ${notif.icono}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="fw-semibold">${notif.titulo}</div>
                        <div class="small text-muted">${notif.mensaje}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                    ${newBadge}
                </div>
            </li>
        `;
    }

    setupNotificationItemListeners() {
        const container = document.getElementById('notifications-list');
        container.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const notifId = item.dataset.id;
                this.manejarClicNotificacion(notifId, item);
            });
        });
    }

    // ==========================
    // MANEJAR NOTIFICACIONES GLOBALES
    // ==========================
    manejarNotificacionGlobal(notificacion) {
        console.log("🎯 Procesando notificación:", notificacion.tipo);

        // Actualizar contador
        if (!notificacion.leida) {
            const currentCount = parseInt(document.getElementById('notification-count').textContent || '0');
            this.actualizarBadgeNotificaciones(currentCount + 1);
        }

        // Si el dropdown está abierto, actualizar la lista
        const dropdown = document.getElementById('notificationsDropdown');
        if (dropdown && dropdown.classList.contains('show')) {
            this.cargarNotificacionesDropdown();
        }

        // Mostrar toast para notificaciones generales
        if (notificacion.tipo !== 'nuevo_mensaje') {
            this.mostrarNotificacionToast(notificacion);
        }

        // Manejar tipos específicos
        this.manejarTipoEspecifico(notificacion);
    }

    manejarTipoEspecifico(notificacion) {
        switch (notificacion.tipo) {
            case 'nuevo_mensaje':
                this.manejarNotificacionMensaje(notificacion);
                break;
            case 'solicitud_tutoria':
            case 'solicitud_aceptada':
            case 'solicitud_rechazada':
                // Lógica específica para tutorías
                break;
        }
    }

    manejarNotificacionMensaje(notificacion) {
        // Esta función puede ser sobrescrita por chat.js
        if (typeof window.manejarNotificacionMensaje === 'function') {
            window.manejarNotificacionMensaje(notificacion);
        }
    }

    // ==========================
    // ACCIONES DE NOTIFICACIONES
    // ==========================
    manejarClicNotificacion(notifId, element) {
        this.marcarComoLeida(notifId, element);
        this.redirigirSegunNotificacion(notifId);
    }

    marcarComoLeida(notifId, element) {
        fetch(`/notificaciones/${notifId}/marcar-leida/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.success) {
                element.classList.remove('unread');
                element.querySelector('.badge')?.remove();
                
                const currentCount = parseInt(document.getElementById('notification-count').textContent);
                this.actualizarBadgeNotificaciones(Math.max(0, currentCount - 1));
            }
        })
        .catch(err => console.error('❌ Error marcando como leída:', err));
    }

    marcarTodasComoLeidas() {
        fetch('/notificaciones/marcar-todas-leidas/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.success) {
                document.querySelectorAll('.notification-item.unread').forEach(item => {
                    item.classList.remove('unread');
                    item.querySelector('.badge')?.remove();
                });
                this.actualizarBadgeNotificaciones(0);
            }
        })
        .catch(err => console.error('❌ Error marcando todas como leídas:', err));
    }

    // ==========================
    // TOASTS DE NOTIFICACIONES
    // ==========================
    mostrarNotificacionToast(notificacion) {
        const toastId = 'toast-' + Date.now();
        const toastHtml = this.getToastHTML(notificacion, toastId);
        
        const toastContainer = document.getElementById('toast-container') || this.crearToastContainer();
        toastContainer.innerHTML += toastHtml;
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        
        toastElement.addEventListener('click', () => {
            this.redirigirSegunNotificacionData(notificacion);
        });
        
        toast.show();
    }

    getToastHTML(notificacion, toastId) {
        return `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${notificacion.color} text-white">
                    <i class="bi ${notificacion.icono} me-2"></i>
                    <strong class="me-auto">${notificacion.titulo}</strong>
                    <small>ahora</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${notificacion.mensaje}
                    ${notificacion.datos_extra ? `<br><small class="text-muted">Haz clic para más detalles</small>` : ''}
                </div>
            </div>
        `;
    }

    crearToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    // ==========================
    // REDIRECCIONES
    // ==========================
    redirigirSegunNotificacion(notifId) {
        // Implementar según necesidad específica
        console.log('Redirigiendo para notificación:', notifId);
    }

    redirigirSegunNotificacionData(notificacion) {
        switch (notificacion.tipo) {
            case 'nuevo_mensaje':
                if (notificacion.datos_extra?.chat_id) {
                    window.location.href = `/chat/?chat_id=${notificacion.datos_extra.chat_id}`;
                }
                break;
            case 'solicitud_tutoria':
                window.location.href = '/tutorias/solicitudes/';
                break;
            case 'solicitud_aceptada':
            case 'solicitud_rechazada':
                window.location.href = '/tutorias/mis-solicitudes/';
                break;
        }
    }

    // ==========================
    // UTILIDADES
    // ==========================
    calcularTiempoTranscurrido(fechaCreacion) {
        const ahora = new Date();
        const fecha = new Date(fechaCreacion);
        const diffMs = ahora - fecha;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Ahora mismo';
        if (diffMins < 60) return `Hace ${diffMins} min`;
        if (diffHours < 24) return `Hace ${diffHours} h`;
        if (diffDays === 1) return 'Ayer';
        if (diffDays < 7) return `Hace ${diffDays} días`;
        
        return fecha.toLocaleDateString();
    }

    getCookie(name) {
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
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.notificationManager = new NotificationManager();
});