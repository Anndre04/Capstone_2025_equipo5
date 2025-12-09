let notiSocket;
const notiMostradas = new Set();
let rolActual = sessionStorage.getItem("rol_actual");


// --------------------
// Funciones de utilidad
// --------------------
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

function actualizarBadge() {
    fetch("/notificaciones/no-leidas/")
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById("notification-count");
            badge.textContent = data.count;
        })
        .catch(err => console.error("Error actualizando badge:", err));
}

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

function marcarTodasNotificaciones() {
    fetch("/notificaciones/marcar-todas-leidas/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({})
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("✅ Todas las notificaciones marcadas como leídas");
                actualizarBadge();
            } else {
                console.error("❌ Error marcando todas las notificaciones:", data.error);
            }
        })
        .catch(err => console.error("❌ Error en fetch:", err));
}

// --------------------
// Funciones de UI
// --------------------

function agregarNotificacionAlDropdown(n) {
    const list = document.getElementById("notifications-list");
    // 1. Cambiamos de <li> a <div> para replicar la estructura de renderizado
    const item = document.createElement("div");

    // 2. Aplicamos las clases exactas de la función de renderizado, 
    //    incluida la lógica condicional para 'bg-light'
    item.className = `notification-item p-2 border-bottom ${n.leida ? '' : 'bg-light'}`;

    item.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div class="d-flex align-items-center">
                <i class="${n.icono} me-2" style="color: ${n.color};"></i>
                <div>
                    <strong>${n.titulo}</strong>
                    <p class="mb-0 small d-inline-block text-truncate" style="max-width: 200px;">${n.mensaje}</p>                
                </div>
            </div>
            <small class="text-muted">${new Date(n.fecha_creacion).toLocaleString()}</small>
        </div>
    `;

    console.log(n)

    item.addEventListener("click", () => {
        marcarNotificacionLeida(n.id, item);
        if (n.datos_extra && n.datos_extra.url) {
            window.location.href = `/${n.datos_extra.url}`;
        }
    });

    // Usar prepend en la lista para que la nueva notificación aparezca al principio
    list.prepend(item);
    actualizarBadge();
}

async function mostrarModalNotificacion(n) {
    if (notiMostradas.has(n.id)) return;
    notiMostradas.add(n.id);

    const rolRequerido = n.datos_extra?.rol_requerido || "Estudiante";
    if (rolActual !== rolRequerido) {
        Swal.fire({
            title: n.titulo,
            html: `<p class="fs-5 text-center">${n.mensaje}</p>
                   <p class="text-danger text-center mt-3">
                        Debes cambiarte al rol <strong>${rolRequerido}</strong> para aceptar esta tutoría.
                   </p>`,
            icon: "warning",
            confirmButtonText: "Entendido",
            customClass: { confirmButton: "btn btn-secondary" },
            buttonsStyling: false
        });
        return;
    }

    marcarNotificacionLeida(n.id);

    const solicitud_id = n.datos_extra.solicitud_id;

    // Modal de confirmación
    const modalConfirm = BS5Helper.Modal.confirmacion({
        titulo: `<strong>${n.titulo}</strong>`,
        mensaje: `<p class="fs-5 text-center">${n.mensaje}</p>
                  <p class="text-muted text-center mt-2">¿Deseas aceptar esta tutoría?</p>`,
        tipo: "info",
        textoSi: "Aceptar",
        textoNo: "Rechazar",
        eliminar: 0
    });

    // Polling simple para verificar cancelación
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/estado-cancelado/${solicitud_id}/`);
            if (!res.ok) return; // si 404, no hacer nada
            const data = await res.json();
            if (data.cancelada) {
                clearInterval(interval);
                BS5Helper.Modal.close(id="bs5-helper-confirmacion");
                BS5Helper.Modal.modalIcono({
                    titulo: "Solicitud cancelada",
                    mensaje: "El tutor ha cancelado la solicitud.",
                    tipo: "danger"
                });
            }
        } catch (e) {
            console.error("Error verificando cancelación:", e);
        }
    }, 1000);

    // Manejar respuesta del modal
    modalConfirm.then(confirmado => {
        clearInterval(interval); // detener polling al decidir
        if (confirmado) {
            fetch(`/aceptar_tutoria/${solicitud_id}/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") }
            }).then(res => res.json())
              .then(data => {
                  if (data.success && data.redirect_url) {
                      BS5Helper.Modal.modalIcono({
                          titulo: "Tutoría aceptada",
                          mensaje: "Redirigiendo...",
                          tipo: "success",
                          cerrar: false,
                          redirigiendo: 1
                      });
                      setTimeout(() => { window.location.href = data.redirect_url; }, 3000);
                  } else location.reload();
              });
        } else {
            fetch(`/rechazar_tutoria/${solicitud_id}/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") }
            }).then(() => location.reload());
        }
    });
}


async function cargarNotificacionesPendientes() {
    const rolActual = sessionStorage.getItem("rol_actual"); // el rol del usuario en esta sesión

    try {
        const res = await fetch('/notificaciones/lista/'); // endpoint de lista
        const data = await res.json();

        if (!data.notificaciones) return;

        for (const n of data.notificaciones) {
            // Solo tutorías no leídas y que requieren este rol
            if (!n.leida && n.tipo === "Solicitud_tutoria" && n.datos_extra?.rol_requerido === rolActual) {
                // Mostrar modal
                await mostrarModalNotificacion(n);

                // Marcar como leída para que no aparezca otra vez
                fetch(`/notificaciones/${n.id}/marcar-leida/`, { method: "POST" });
            }
        }
    } catch (err) {
        console.error("Error cargando notificaciones pendientes:", err);
    }
}

// ================================
// 🔹 Función general de alerta
// ================================
/*function mostrarAlertaTutoría(data) {
    return Swal.fire({
        icon: data.icon || 'info',
        title: data.titulo || 'Notificación',
        text: data.mensaje || '',
        confirmButtonText: data.confirmButtonText || 'Aceptar',
        customClass: { confirmButton: 'btn btn-primary' },
        buttonsStyling: false
    });
}*/

// ================================
// 🔹 Modal para reseña
// ================================
async function mostrarModalReseña(tutoriaId, comentariosPredefinidos) {

    const conf = await BS5Helper.Modal.confirmacion({
        titulo: "La tutoría ha finalizado.",
        mensaje: "¿Deseas dejar una reseña de esta tutoría?",
        tipo: "info",
        textoSi: "Sí",
        textoNo: "No"
    });

    if (!conf) {
        window.location.href = "/";
        return;
    }

    let seleccion = 1;
    let modalActual = null; // ⬅️ Aquí guardaremos el modal

    const estrellasHtml = Array.from({ length: 5 }, (_, i) =>
        `<span class="estrella" data-value="${i + 1}"
            style="font-size:2rem; cursor:pointer; color:${i === 0 ? 'gold' : 'gray'};">
            ${i === 0 ? '★' : '☆'}
        </span>`
    ).join('');

    const comentariosHtml = comentariosPredefinidos.map(c =>
        `<label class="d-block mt-1">
            <input type="checkbox" value="${c.id}"> ${c.comentario}
        </label>`
    ).join('');

    const resultado = await BS5Helper.Modal.custom({
        titulo: "Deja tu reseña",
        size: "modal-lg",
        textoSi: "Enviar",
        html: `
            <div class="text-center mb-3">${estrellasHtml}</div>
            <div>${comentariosHtml}</div>
        `,
        onOpen: (modal) => {

            modalActual = modal; // ⬅️ Guardamos el modal DOM real

            const estrellas = modal.querySelectorAll(".estrella");

            const pintar = (hasta) => {
                estrellas.forEach((s, i) => {
                    s.textContent = i < hasta ? "★" : "☆";
                    s.style.color = i < hasta ? "gold" : "gray";
                });
            };

            pintar(seleccion);

            estrellas.forEach(star => {
                star.addEventListener("mouseover", () => pintar(parseInt(star.dataset.value)));
                star.addEventListener("click", () => {
                    seleccion = parseInt(star.dataset.value);
                    pintar(seleccion);
                });
                star.addEventListener("mouseout", () => pintar(seleccion));
            });
        }
    });

    if (!resultado) {
        window.location.href = "/";
        return;
    }

    // Recolectar checkboxes ✔ CORREGIDO
    const comentarios = Array.from(
        modalActual.querySelectorAll('input[type="checkbox"]:checked')
    ).map(c => c.value);

    console.log("Selección estrellas:", seleccion);
    console.log("Comentarios seleccionados:", comentarios);

    const data = new URLSearchParams();
    data.append("estrellas", seleccion);
    comentarios.forEach(id => data.append("comentarios[]", id));

    try {
        const response = await fetch(`/tutoria/reseña/${tutoriaId}/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: data
        });

        const result = await response.json();

        if (result.success) {
            BS5Helper.Modal.modalIcono({
                titulo: "Gracias",
                mensaje: "Tu reseña ha sido enviada",
                tipo: "success",
                redirigiendo: 1
            });
            window.location.href = "/";
        }
    } catch (err) {
        console.error(err);
        BS5Helper.Modal.alerta({
            titulo: "Error",
            mensaje: "No se pudo enviar la reseña",
            tipo: "danger"
        });
    }
}


// --------------------
// WebSocket
// --------------------
function conectarNotificaciones() {
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const notiSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/notificaciones/`);

    notiSocket.onopen = () => console.log("✅ Conectado al WebSocket de notificaciones");

    actualizarBadge();

    notiSocket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        console.log("📩 WS mensaje recibido:", data);

        // =========================================================

        if (rolActual === "Estudiante" && data.tipo === "tutoria_finalizada") {
            const tutoriaId = data.datos_extra?.tutoria_id;
            const comentarios = data.datos_extra?.comentarios_predefinidos || [];

            if (tutoriaId) {
                mostrarModalReseña(tutoriaId, comentarios);
            } else {
                console.error("❌ tutoriaId no definido en datos_extra", data);
            }
        } else if (rolActual === "Tutor" && data.tipo === "tutoria_finalizada") {
            window.BS5Helper.Modal.alerta({
                titulo: `<strong>${data.titulo}</strong>`,
                mensaje: data.mensaje,
                texto: "OK"
            }).then(() => {
                if (typeof window.disableUnloadProtection === "function") {
                    window.disableUnloadProtection();
                }
                window.location.href = "/tutoria/gestortutorias";
            });
        }

        if (data.tipo === "Solicitud_tutoria") {
            mostrarModalNotificacion(data);
        }

        if (data.tipo === "nuevo_mensaje" || data.tipo === "solicitud_alumno") {
            if (window.BS5Helper && window.BS5Helper.Toast) {
                window.BS5Helper.Toast.mostrar({
                    mensaje: `<strong>${data.titulo}</strong>`,
                    tipo: "primary",
                    duracion: 8000,
                    posicion: "top-end"
                });
            }
        }

        agregarNotificacionAlDropdown(data);
        actualizarBadge();
    };

    notiSocket.onclose = (e) => console.log("❌ WebSocket cerrado:", e);
    notiSocket.onerror = (err) => console.error("❌ Error en WebSocket:", err);
}

async function cargarNotificaciones() {
    const lista = document.getElementById('notifications-list');
    if (!lista) return;

    try {
        const res = await fetch('/notificaciones/lista/');
        const data = await res.json();

        // Limpiar contenido actual
        lista.innerHTML = '';

        if (!data.notificaciones || data.notificaciones.length === 0) {
            lista.innerHTML = `
                <div class="text-center py-3 text-muted">
                    <i class="bi bi-bell-slash display-6"></i>
                    <p class="mb-0 small">No hay notificaciones</p>
                </div>
            `;
            return;
        }

        // Renderizar cada notificación
        data.notificaciones.forEach(n => {
            const div = document.createElement('div');
            div.className = `notification-item p-2 border-bottom ${n.leida ? '' : 'unread'}`;
            div.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="d-flex align-items-center">
                        <i class="${n.icono} me-2" style="color: ${n.color};"></i>
                        <div>
                            <strong>${n.titulo}</strong>
                            <p class="mb-0 small d-inline-block text-truncate" style="max-width: 200px;">${n.mensaje}</p>                
                        </div>
                    </div>
                    <small class="text-muted">${new Date(n.fecha_creacion).toLocaleString()}</small>
                </div>
            `;
            lista.appendChild(div);
        });

    } catch (err) {
        console.error('❌ Error cargando notificaciones:', err);
        lista.innerHTML = `
            <div class="text-center py-3 text-danger">
                <p class="mb-0 small">Error al cargar notificaciones</p>
            </div>
        `;
    }
}
// --------------------
// Inicialización
// --------------------
document.addEventListener("DOMContentLoaded", () => {
    conectarNotificaciones();
    cargarNotificacionesPendientes()
    cargarNotificaciones()

    const btnMarcarTodas = document.getElementById("mark-all-read");
    if (btnMarcarTodas) {
        btnMarcarTodas.addEventListener("click", () => {
            marcarTodasNotificaciones();
        });
    }
});
