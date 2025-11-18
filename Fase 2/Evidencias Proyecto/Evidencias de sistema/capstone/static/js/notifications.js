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
                     ⚠️ Debes cambiarte al rol <strong>${rolRequerido}</strong> para aceptar esta tutoría.
                   </p>`,
            icon: "warning",
            confirmButtonText: "Entendido",
            customClass: { confirmButton: "btn btn-secondary" },
            buttonsStyling: false
        });
        return;
    }

    // Marcar como leída de inmediato
    marcarNotificacionLeida(n.id);

    // Modal de acción si rol coincide
    Swal.fire({
        title: n.titulo,
        html: `<p class="fs-5 text-center">${n.mensaje}</p>
               <p class="text-muted text-center mt-2">¿Deseas aceptar esta tutoría?</p>`,
        icon: "question",
        showCancelButton: true,
        confirmButtonText: "Aceptar",
        cancelButtonText: "Rechazar",
        customClass: { confirmButton: "btn btn-success", cancelButton: "btn btn-danger" },
        buttonsStyling: false
    }).then((result) => {
        const solicitud_id = n.datos_extra.solicitud_id;
        if (result.isConfirmed) {
            fetch(`/aceptar_tutoria/${solicitud_id}/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.redirect_url) {
                        window.location.href = data.redirect_url; // 🔥 redirección real
                    } else if (data.error) {
                        Swal.fire("Error", data.error, "error");
                    } else {
                        location.reload(); // fallback si no es tutoría
                    }
                })
                .catch(() => Swal.fire("Error", "Ocurrió un problema al aceptar la tutoría", "error"));

        } else if (result.dismiss === Swal.DismissReason.cancel) {
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
    const confirmacion = await Swal.fire({
        icon: 'question',
        title: 'La tutoría ha finalizado.',
        text: '¿Deseas dejar una reseña de esta tutoría?',
        showCancelButton: true,
        confirmButtonText: 'Sí',
        cancelButtonText: 'No',
        allowOutsideClick: false,
        allowEscapeKey: false,
        customClass: { confirmButton: 'btn btn-primary', cancelButton: 'btn btn-secondary' },
        buttonsStyling: false
    });

    if (!confirmacion.isConfirmed) return;

    let seleccion = 1; // 🔹 Declarada aquí para usarla en preConfirm

    const estrellasHtml = Array.from({ length: 5 }, (_, i) =>
        `<span class="estrella" data-value="${i + 1}" style="font-size:2rem; cursor:pointer; color: ${i === 0 ? 'gold' : 'gray'};">
            ${i === 0 ? '★' : '☆'}
        </span>`
    ).join('');

    const comentariosHtml = comentariosPredefinidos.map(c =>
        `<label style="display:block; margin:5px 0;">
            <input type="checkbox" value="${c.id}"> ${c.comentario}
        </label>`
    ).join('');

    try {
        const { value: formValues } = await Swal.fire({
            title: 'Deja tu reseña',
            html: `
                <div style="text-align:center; margin-bottom:10px;">
                    ${estrellasHtml}
                </div>
                <div style="text-align:left; margin-top:10px;">
                    ${comentariosHtml}
                </div>
            `,
            focusConfirm: false,
            showCancelButton: true,
            confirmButtonText: 'Enviar',
            cancelButtonText: 'Cancelar',
            allowOutsideClick: false,
            allowEscapeKey: false,
            customClass: { confirmButton: 'btn btn-primary', cancelButton: 'btn btn-secondary' },
            buttonsStyling: false,
            didOpen: () => {
                const estrellas = Swal.getPopup().querySelectorAll('.estrella');

                const pintarEstrellas = (hasta) => {
                    estrellas.forEach((s, i) => {
                        s.textContent = i < hasta ? '★' : '☆';
                        s.style.color = i < hasta ? 'gold' : 'gray';
                    });
                };

                pintarEstrellas(seleccion); // primera estrella marcada

                estrellas.forEach(star => {
                    star.addEventListener('mouseover', () => {
                        const val = parseInt(star.dataset.value);
                        pintarEstrellas(val);
                    });
                    star.addEventListener('click', () => {
                        seleccion = parseInt(star.dataset.value); // actualiza selección
                        pintarEstrellas(seleccion);
                    });
                    star.addEventListener('mouseout', () => {
                        pintarEstrellas(seleccion);
                    });
                });
            },
            preConfirm: () => {
                const comentarios = Array.from(
                    Swal.getPopup().querySelectorAll('input[type="checkbox"]:checked')
                ).map(c => c.value);
                return { estrellas: seleccion, comentarios };
            }
        });

        if (!formValues) return;

        const data = new URLSearchParams();
        data.append("estrellas", formValues.estrellas);
        formValues.comentarios.forEach(id => data.append("comentarios[]", id));

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
            Swal.fire('Gracias', 'Tu reseña ha sido enviada', 'success');
        }
    } catch (err) {
        console.error("❌ Error enviando reseña:", err);
        Swal.fire('Error', 'No se pudo enviar la reseña', 'error');
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
        } else if ((rolActual === "Tutor" && data.tipo === "tutoria_finalizada")) {
            Swal.fire({
                icon: "info",
                title: "Tutoría finalizada",
                text: "La tutoria ha finiquitado.",
                confirmButtonText: "Aceptar",
                customClass: { confirmButton: 'btn btn-primary' },
                buttonsStyling: false
            });
        }


        if (data.tipo === "Solicitud_tutoria") {
            mostrarModalNotificacion(data);
        }

        if (data.tipo === "nuevo_mensaje") {
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
