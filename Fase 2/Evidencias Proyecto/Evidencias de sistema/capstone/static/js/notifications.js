let notiSocket;
const notiMostradas = new Set();

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
function mostrarToastNotificacion(n) {
    if (notiMostradas.has(n.id)) return;
    notiMostradas.add(n.id);

    const container = document.getElementById("noti-toast-container");

    const toast = document.createElement("div");
    toast.className = "toast align-items-center text-bg-primary border-0";
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "assertive");
    toast.setAttribute("aria-atomic", "true");

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${n.titulo}</strong><br>
                <small>${n.mensaje}</small>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { autohide: false });
    bsToast.show();

    toast.addEventListener("hidden.bs.toast", () => toast.remove());
}

function agregarNotificacionAlDropdown(n) {
    const list = document.getElementById("notifications-list");
    const item = document.createElement("li");
    item.className = "dropdown-item fw-bold";
    item.innerHTML = `
        <i class="${n.icono} text-${n.color} me-2"></i>
        ${n.titulo} - <small>${n.mensaje}</small>`;

    item.addEventListener("click", () => {
        marcarNotificacionLeida(n.id, item);
        if (n.datos_extra && n.datos_extra.url) {
            window.location.href = `/${n.datos_extra.url}`;
        }
    });

    list.prepend(item);
    actualizarBadge();
}

async function mostrarModalNotificacion(n) {
    if (notiMostradas.has(n.id)) return;
    notiMostradas.add(n.id);

    const rolActual = sessionStorage.getItem("rol_actual");
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
    marcarNotificacionLeida(n.id)
    
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
            }).then(() => location.reload());
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


// --------------------
// WebSocket
// --------------------
function conectarNotificaciones() {
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    notiSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/notificaciones/`);

    notiSocket.onopen = () => console.log("✅ Conectado al WebSocket de notificaciones");

    notiSocket.onmessage = (e) => {
        const data = JSON.parse(e.data);

        console.log(data)

        if (data.tipo === "Solicitud_tutoria") {
            mostrarModalNotificacion(data);
        }

        agregarNotificacionAlDropdown(data);
        actualizarBadge();
    };

    notiSocket.onclose = (e) => console.log("❌ WebSocket de notificaciones cerrado", e);
    notiSocket.onerror = (err) => console.error("❌ Error WebSocket de notificaciones", err);
}

// --------------------
// Inicialización
// --------------------
document.addEventListener("DOMContentLoaded", () => {
    cargarNotificacionesPendientes()
    conectarNotificaciones();
    cargarNotificacionesDropdown();

    const btnMarcarTodas = document.getElementById("mark-all-read");
    if (btnMarcarTodas) {
        btnMarcarTodas.addEventListener("click", () => {
            marcarTodasNotificaciones();
        });
    }
});
