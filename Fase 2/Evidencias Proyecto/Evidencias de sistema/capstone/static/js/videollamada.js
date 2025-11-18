const callTimer = document.getElementById('callTimer');
let elapsedTime = Number(callTimer.dataset.elapsed) || 0;

function updateCallTimer() {
    const minutes = Math.floor(elapsedTime / 60);
    const seconds = elapsedTime % 60;
    document.getElementById('callTimer').textContent =
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    elapsedTime++;
}

// Llamamos cada segundo
updateCallTimer(); // Actualiza inmediatamente
setInterval(updateCallTimer, 1000);

let currentAudioEnabled = false;   // micrófono activado
let currentVideoEnabled = true;

// Mejorar indicadores de micrófono y cámara locales
function updateLocalIndicators() {
    const micIndicator = document.getElementById('localMicIndicator');
    const camIndicator = document.getElementById('localCamIndicator');

    if (micIndicator) {
        micIndicator.className = currentAudioEnabled ?
            'bi bi-mic-fill text-success' : 'bi bi-mic-mute-fill text-danger';
    }

    if (camIndicator) {
        camIndicator.className = currentVideoEnabled ?
            'bi bi-camera-video-fill text-success' : 'bi bi-camera-video-off-fill text-danger';
    }
}

// Sobrescribir funciones de toggle para actualizar indicadores
const originalToggleMic = window.toggleMic;
window.toggleMic = function () {
    if (originalToggleMic) originalToggleMic();
    updateLocalIndicators();
};

const originalToggleCam = window.toggleCam;
window.toggleCam = function () {
    if (originalToggleCam) originalToggleCam();
    updateLocalIndicators();
};

class FileCustomizer {
    // ... (Constructor, updateFiles, renderFileList, updateFileInput, handleRemoveClick
    //      son idénticos a la implementación anterior) ...
    constructor(fileInputId, listId) {
        this.fileInput = document.getElementById(fileInputId);
        this.listaArchivos = document.getElementById(listId);
        this.errorMessage = document.getElementById('file-error-message');

        if (!this.fileInput || !this.listaArchivos) return;

        this.selectedFiles = [];
        this.fileNames = [];

        this.listaArchivos.addEventListener('click', this.handleRemoveClick.bind(this));
        this.fileInput.addEventListener('change', this.updateFiles.bind(this));

        this.renderFileList();
    }

    updateFiles() {
        const newFiles = Array.from(this.fileInput.files);
        this.selectedFiles = newFiles;
        this.fileNames = new Array(newFiles.length).fill(null);
        this.renderFileList();
    }

    renderFileList() {
        this.listaArchivos.innerHTML = '';
        this.errorMessage.classList.add('d-none');

        if (this.selectedFiles.length === 0) {
            const li = document.createElement('li');
            li.className = 'list-group-item text-muted';
            li.textContent = 'Ningún archivo seleccionado.';
            this.listaArchivos.appendChild(li);
            return;
        }

        this.selectedFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex align-items-center justify-content-between p-2';

            // Creación de elementos...
            const fileInfoContainer = document.createElement('div');
            fileInfoContainer.className = 'd-flex align-items-center flex-grow-1';

            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'btn btn-sm btn-outline-danger me-2 p-1';
            removeButton.innerHTML = '<i class="bi bi-x"></i>';
            removeButton.setAttribute('data-index', index);
            removeButton.title = 'Eliminar este archivo';
            removeButton.dataset.action = 'remove-file';

            const filenameSpan = document.createElement('span');
            filenameSpan.className = 'fw-medium text-truncate small me-3';
            filenameSpan.textContent = file.name;

            fileInfoContainer.appendChild(removeButton);
            fileInfoContainer.appendChild(filenameSpan);

            const inputName = document.createElement('input');
            inputName.type = 'text';
            inputName.name = `nombre_archivo_${index}`;
            inputName.placeholder = 'Nombre para guardar (sin extensión)';
            inputName.className = 'form-control form-control-sm w-50';
            inputName.maxLength = 80;

            const initialName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
            inputName.value = this.fileNames[index] || initialName;

            inputName.addEventListener('input', (e) => {
                this.fileNames[index] = e.target.value;
            });

            li.appendChild(fileInfoContainer);
            li.appendChild(inputName);
            this.listaArchivos.appendChild(li);
        });

        this.updateFileInput();
    }

    updateFileInput() {
        try {
            const dataTransfer = new DataTransfer();
            this.selectedFiles.forEach(file => {
                dataTransfer.items.add(file);
            });
            this.fileInput.files = dataTransfer.files;
        } catch (e) {
            this.errorMessage.textContent = 'Tu navegador no soporta la edición de la lista de archivos.';
            this.errorMessage.classList.remove('d-none');
        }
    }

    handleRemoveClick(event) {
        const removeButton = event.target.closest('[data-index]');
        if (removeButton && removeButton.dataset.action === 'remove-file') {
            event.preventDefault();
            const index = parseInt(removeButton.dataset.index);

            if (index >= 0 && index < this.selectedFiles.length) {
                this.selectedFiles.splice(index, 1);
                this.fileNames.splice(index, 1);
                this.renderFileList();
            }
        }
    }

    // Nuevo método para obtener todos los datos, incluidos los nombres personalizados
    getFormData() {
        const formData = new FormData();

        // 1. Agregar los archivos reales del input (ya actualizados por updateFileInput)
        const files = this.fileInput.files;
        for (let i = 0; i < files.length; i++) {
            formData.append('archivo', files[i]);
        }

        // 2. Agregar los nombres personalizados
        this.fileNames.forEach((name, index) => {
            if (name !== null) {
                formData.append(`nombre_archivo_${index}`, name);
            } else if (files[index]) {
                // Si el nombre es null, usar el nombre original (sin extensión) como fallback
                const originalName = files[index].name.substring(0, files[index].name.lastIndexOf('.')) || files[index].name;
                formData.append(`nombre_archivo_${index}`, originalName);
            }
        });

        return formData;
    }
}


// --------------------------------------------------------------------------
// LÓGICA DE SUBIDA AJAX Y MANEJO DE MODAL
// --------------------------------------------------------------------------

const uploadDocumentModal = document.getElementById('uploadDocumentModal');
const formElement = document.getElementById('uploadForm');
const tutoriaIdInput = document.getElementById('tutoriaIdInput');
const confirmUploadBtn = document.getElementById('confirmUploadBtn');

// Instancia del manejador de archivos (CRÍTICO)
const fileCustomizer = new FileCustomizer('id_archivo', 'lista-archivos-seleccionados');

/**
 * Función que maneja el envío AJAX del formulario.
 */
async function handleFormSubmit(event) {
    event.preventDefault(); // Detener la recarga de la página

    const url = formElement.action;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // 1. Deshabilitar botón y mostrar carga
    confirmUploadBtn.disabled = true;
    confirmUploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Subiendo...';

    // 2. Obtener los datos del formulario (archivos, nombres, y tutoria_id)
    const formData = fileCustomizer.getFormData();
    formData.append('tutoria_id', tutoriaIdInput.value); // Añadir el ID de la tutoría

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                // NO establecer Content-Type; el navegador lo hace automáticamente
                // para FormData, incluyendo el boundary.
            },
            body: formData
        });

        const data = await response.json(); // Asumimos que Django devuelve JSON

        if (response.ok) {
            // Éxito: Mostrar mensaje y recargar la lista de archivos (si aplica)

            // 💡 NOTA: messages.success de Django no funciona en AJAX.
            // Usamos un alert o una librería como Toastr/SweetAlert.
            alert(`✅ Éxito: ${data.message || 'Archivos subidos correctamente.'}`);

            // Cerrar modal y posiblemente recargar la sección de la página
            const modal = bootstrap.Modal.getInstance(uploadDocumentModal);
            modal.hide();

            // 🔄 Recargar la ventana o el componente de lista de archivos de la tutoría
            window.location.reload();

        } else {
            // Fallo del servidor (4xx, 5xx)
            alert(`❌ Error al subir: ${data.error || 'Ocurrió un error inesperado en el servidor.'}`);
            console.error('Server error data:', data);
        }

    } catch (error) {
        // Fallo de red o error de JS
        alert('❌ Error de conexión: No se pudo contactar al servidor.');
        console.error('Fetch error:', error);
    } finally {
        // 3. Habilitar botón
        confirmUploadBtn.disabled = false;
        confirmUploadBtn.innerHTML = 'Confirmar Subida';
    }
}

// 4. Conectar el listener del formulario
formElement.addEventListener('submit', handleFormSubmit);


// 5. LÓGICA DE INYECCIÓN DE ID AL ABRIR EL MODAL (Como en el código anterior)
uploadDocumentModal.addEventListener('show.bs.modal', event => {
    const button = event.relatedTarget;
    const tutoriaId = button.getAttribute('data-tutoria-id');
    const tutoriaUrl = button.getAttribute('data-tutoria-url');

    if (tutoriaIdInput) { tutoriaIdInput.value = tutoriaId || ''; }
    if (formElement && tutoriaUrl) { formElement.action = tutoriaUrl; }

    // Resetear el estado del FileCustomizer al abrir
    fileCustomizer.selectedFiles = [];
    fileCustomizer.fileNames = [];
    fileCustomizer.updateFileInput();
    fileCustomizer.renderFileList();
});

let preguntaCount = 0;

// ==============================
// Función de validación
// ==============================
function validarEvaluacion() {
    console.log("📌 Iniciando validación...");

    let valido = true;
    const preguntas = document.querySelectorAll("#preguntasContainer .card");
    const errorPreguntas = document.getElementById("errorPreguntas");

    // Ocultar errores anteriores
    document.querySelectorAll(".text-danger").forEach(e => e.classList.add("d-none"));
    document.querySelectorAll(".is-invalid").forEach(e => e.classList.remove("is-invalid"));

    //1️⃣ Título no vacío
    const titulo = document.getElementById("tituloEvaluacion");
    if (!titulo.value.trim()) {
        marcarError(titulo, "El título de la evaluación es obligatorio.");
        valido = false;
    }

    // 2️⃣ Al menos una pregunta
    if (preguntas.length === 0) {
        console.log("❌ No hay preguntas");
        if (errorPreguntas) errorPreguntas.classList.remove("d-none");
        valido = false;
    }

    // 3️⃣ Validar cada pregunta
    preguntas.forEach((pregunta, index) => {
        const inputPregunta = pregunta.querySelector("input[type='text']:not([name*='_opcion_'])");
        const inputPuntos = pregunta.querySelector("input[type='number']");
        const opciones = pregunta.querySelectorAll(".input-group");

        // Contenido de pregunta
        if (!inputPregunta.value.trim()) {
            marcarError(inputPregunta, "La pregunta no puede estar vacía.");
            valido = false;
            return;
        }

        // Puntos válidos
        if (!inputPuntos.value || parseInt(inputPuntos.value) <= 0) {
            marcarError(inputPuntos, "Los puntos deben ser mayores que 0.");
            valido = false;
            return;
        }

        // Al menos 2 opciones
        if (opciones.length < 2) {
            marcarError(pregunta, "La pregunta debe tener al menos 2 opciones.");
            valido = false;
            return;
        }

        // Opciones no vacías
        const inputVacio = Array.from(opciones).find(op => !op.querySelector("input[type='text']").value.trim());
        if (inputVacio) {
            marcarError(inputVacio.querySelector("input[type='text']"), "Hay una opción vacía.");
            valido = false;
            return;
        }

        // Opción correcta seleccionada
        const correcta = pregunta.querySelector("input[type='radio']:checked");
        if (!correcta) {
            marcarError(pregunta, "Debe marcar una opción correcta.");
            valido = false;
            return;
        }
    });

    return valido; // ✅ Devuelve true si todo está bien
}

// ==============================
// Función para enviar AJAX
// ==============================
function enviarEvaluacion() {
    const form = document.getElementById("crearEvaluacionForm");

    if (!validarEvaluacion()) {
        console.log("❌ Validación fallida, no se envía el formulario");
        return;
    }

    console.log("✅ Validación correcta, enviando AJAX...");

    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            console.log("📦 Respuesta del servidor:", data);

            if (data.status === 'success') {
                window.showAlert(data.message, 'success');

                // Reset formulario y modal
                form.reset();
                document.getElementById("preguntasContainer").innerHTML = '';
                preguntaCount = 0;

                const modalEl = document.getElementById("crearEvaluacionModal");
                const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.hide();
            } else {
                window.showAlert(data.message || 'Ocurrió un error', 'error');
            }
        })
        .catch(error => {
            window.showAlert('Hubo un error en su solicitud', 'error');
        });
}

// ==============================
// Función para mostrar errores
// ==============================
function marcarError(elemento, mensaje) {
    let small = elemento.parentElement.querySelector(".text-danger");

    if (!small) {
        small = document.createElement("small");
        small.className = "text-danger d-flex align-items-center gap-1 mt-1";
        small.innerHTML = `<i class="bi bi-exclamation-circle-fill"></i> ${mensaje}`;
        elemento.parentElement.appendChild(small);
    } else {
        small.innerHTML = `<i class="bi bi-exclamation-circle-fill"></i> ${mensaje}`;
    }

    small.classList.remove("d-none");
    elemento.classList.add("is-invalid");
    elemento.scrollIntoView({ behavior: "smooth", block: "center" });
    elemento.focus();
}

document.getElementById("btnenviarEvaluacion").addEventListener("click", function (e) {
    e.preventDefault();
    enviarEvaluacion();
});

document.getElementById("btnAgregarPregunta").addEventListener("click", function (e) {
    e.preventDefault();
    agregarPregunta();
});

function agregarPregunta() {
    preguntaCount++;
    const preguntaId = preguntaCount;

    const divPregunta = document.createElement("div");
    divPregunta.classList.add("card", "mb-3", "p-3");
    divPregunta.dataset.id = preguntaId;

    divPregunta.innerHTML = `
    <div class="d-flex justify-content-between align-items-center mb-2">
        <h5 class="mb-0">Pregunta ${preguntaId}</h5>
        <button type="button" class="btn btn-danger btn-sm" onclick="eliminarPregunta(${preguntaId})">
        <i class="bi bi-trash"></i> Eliminar Pregunta
        </button>
    </div>

    <input type="text" name="pregunta_${preguntaId}" class="form-control mb-2" placeholder="Texto de la pregunta">

    <input type="number" name="pregunta_${preguntaId}_puntos" class="form-control mb-2" min="1" placeholder="Puntos de la pregunta">

    <div id="opcionesContainer_${preguntaId}"></div>

    <button type="button" class="btn btn-outline-primary btn-sm" onclick="agregarOpcion(${preguntaId})">
        <i class="bi bi-plus-circle"></i> Agregar Opción
    </button>
    `;

    document.getElementById("preguntasContainer").appendChild(divPregunta);

    // Agrega dos opciones iniciales
    setTimeout(() => {
        agregarOpcion(preguntaId);
        agregarOpcion(preguntaId);
    }, 50);
}

function agregarOpcion(preguntaId) {
    const contenedorOpciones = document.getElementById(`opcionesContainer_${preguntaId}`);
    if (!contenedorOpciones) return;

    const opcionCount = contenedorOpciones.querySelectorAll(".input-group").length + 1;

    const divOpcion = document.createElement("div");
    divOpcion.classList.add("input-group", "mb-2");
    divOpcion.innerHTML = `
    <div class="input-group-text">
      <input type="radio" name="pregunta_${preguntaId}_correcta" value="${opcionCount}" required>
    </div>
    <input type="text" name="pregunta_${preguntaId}_opcion_${opcionCount}" class="form-control" placeholder="Opción ${opcionCount}" required>
    <button class="btn btn-outline-danger" type="button" onclick="eliminarOpcion(${preguntaId}, this)">
      <i class="bi bi-x-circle"></i>
    </button>
  `;

    contenedorOpciones.appendChild(divOpcion);
}

function eliminarPregunta(preguntaId) {
    const pregunta = document.querySelector(`[data-id="${preguntaId}"]`);
    if (pregunta) pregunta.remove();
    reindexarPreguntas();
}

function eliminarOpcion(preguntaId, boton) {
    boton.closest(".input-group").remove();
    reindexarOpciones(preguntaId);
}

function reindexarPreguntas() {
    const preguntas = document.querySelectorAll("#preguntasContainer .card");
    preguntas.forEach((pregunta, index) => {
        const nuevoId = index + 1;
        pregunta.dataset.id = nuevoId;
        pregunta.querySelector("h5").textContent = `Pregunta ${nuevoId}`;
        pregunta.querySelector("input[type='text']").name = `pregunta_${nuevoId}`;

        const eliminarBtn = pregunta.querySelector(".btn-danger");
        eliminarBtn.setAttribute("onclick", `eliminarPregunta(${nuevoId})`);

        const opcionesContainer = pregunta.querySelector(`[id^="opcionesContainer_"]`);
        opcionesContainer.id = `opcionesContainer_${nuevoId}`;

        const agregarBtn = pregunta.querySelector(".btn-outline-primary");
        agregarBtn.setAttribute("onclick", `agregarOpcion(${nuevoId})`);

        reindexarOpciones(nuevoId);
    });
    preguntaCount = preguntas.length;
}

function reindexarOpciones(preguntaId) {
    const contenedorOpciones = document.getElementById(`opcionesContainer_${preguntaId}`);
    if (!contenedorOpciones) return;

    const opciones = contenedorOpciones.querySelectorAll(".input-group");
    opciones.forEach((opcion, index) => {
        const nuevoIndex = index + 1;
        const radio = opcion.querySelector("input[type='radio']");
        const texto = opcion.querySelector("input[type='text']");
        radio.name = `pregunta_${preguntaId}_correcta`;
        radio.value = nuevoIndex;
        texto.name = `pregunta_${preguntaId}_opcion_${nuevoIndex}`;
        texto.placeholder = `Opción ${nuevoIndex}`;
    });
}




document.addEventListener("DOMContentLoaded", function () {

    // --- 1. Obtener CONFIGURACIÓN ---
    const info = document.getElementById("info");
    const USER_ID = info.dataset.user;
    const TUTORIA_ID = info.dataset.tutoriaId;
    const horaInicio = new Date(info.dataset.horaInicio);
    const horaFin = new Date(info.dataset.horaFin);
    const ROLE = sessionStorage.getItem('rol_actual');

    // --- 2. Obtener REFERENCIAS AL DOM de los BOTONES ---
    const actionsContainer = document.getElementById('botonestutor');
    const btnSubirDocumento = document.getElementById('btnSubirDocumento');
    const btnRealizarEvaluacion = document.getElementById('btnRealizarEvaluacion');
    let btnResponderEvaluacion = document.getElementById('btnResponderEvaluacion'); // puede crearse dinámicamente

    // --- 3. Función para actualizar visibilidad usando clases de BS5 ---
    function updateActionButtonsVisibility() {
        // 1. Ocultar todos los elementos por defecto
        actionsContainer.classList.add('d-none');
        btnSubirDocumento.classList.add('d-none');
        btnRealizarEvaluacion.classList.add('d-none');

        if (!ROLE) {
            console.warn("⚠️ No se encontró la variable ROLE. Todos los botones ocultos.");
            return;
        }

        if (ROLE === 'Tutor') {
            console.log("LOG: Modo Tutor activado. Mostrando botones de Tutor.");

            btnSubirDocumento.classList.remove('d-none');
            btnRealizarEvaluacion.classList.remove('d-none');
            actionsContainer.classList.remove('d-none');
            btnResponderEvaluacion.classList.add('d-none')
        }
        else if (ROLE === 'Estudiante') {
            actionsContainer.classList.remove('d-none');
            console.log("NADA")
        }
        else {
            console.warn(`⚠️ Rol desconocido ('${ROLE}'). Todos los botones ocultos.`);
        }
    }

    // --- 4. Ejecutar la visibilidad de los botones ---
    updateActionButtonsVisibility();

    // --- 5. Lógica de indicadores y FileCustomizer ---
    updateLocalIndicators();

    const fileCustomizer = new FileCustomizer('id_archivo', 'lista-archivos-seleccionados');
    const originalRenderFileList = fileCustomizer.renderFileList;
    fileCustomizer.renderFileList = function () {
        originalRenderFileList.call(this);
        const fileItems = this.listaArchivos.querySelectorAll('li');
        fileItems.forEach(item => item.classList.add('file-item'));
    };
    fileCustomizer.renderFileList();

    // --- 6. Función dinámica para botón de estudiante ---
    function showResponseButtonDynamically(evaluacionId) {
        if (ROLE !== 'Estudiante') return;

        const url = `/evaluaciones/responder/${evaluacionId}/`;

        btnResponderEvaluacion.href = url;
        btnResponderEvaluacion.classList.remove('d-none', 'disabled');

        console.log(`✅ Evaluación ${evaluacionId} publicada. Botón habilitado con link: ${url}`);
    }

    console.log("🕒 Hora de fin de la tutoría:", horaFin);

    // Función para hacer la solicitud AJAX
    function completarTutoria() {
        console.log("🚀 Intentando completar tutoría automáticamente...");
        fetch(`/tutoria/tutoria-completada/${TUTORIA_ID}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log("✅ Tutoria completada automáticamente");
                    clearInterval(intervalId); // detener el intervalo
                } else {
                    console.warn("❌ No se pudo completar la tutoría:", data);
                }
            })
            .catch(err => console.error("⚠️ Error en la solicitud:", err));
    }

    // Función para obtener CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(cookie => {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }

    // Intervalo cada 5 segundos
    const intervalId = setInterval(() => {
        const ahora = new Date();
        console.log("⏱️ Revisando hora actual:", ahora);
        if (ahora >= horaFin) {
            console.log("⌛ La hora de fin ya pasó. Llamando a completarTutoria()");
            completarTutoria();
        }
    }, 5000);
    // --- CONFIGURACIÓN DE CONEXIÓN ---
    console.log("CONFIG: TUTORIA_ID:", TUTORIA_ID, "USER_ID:", USER_ID, "ROLE:", ROLE);
    if (!TUTORIA_ID || TUTORIA_ID.includes('tutoria.id')) {
        console.error("CONFIG ERROR: TUTORIA_ID no está correctamente interpolado por Django.");
    }

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const wsPath = `${wsScheme}://${window.location.host}/ws/tutoria/${TUTORIA_ID}/`;
    console.log("CONFIG: WebSocket Path:", wsPath);

    // --- ESTADO GLOBAL AJUSTADO: Usamos el gestor en lugar del socket directo ---
    let wsManager;

    // --- Estado de la Sesión ---
    let localStream = null;
    let remoteStream = new MediaStream();
    let peerConnection;
    let screenStream;
    let pendingIceCandidates = [];
    let remoteAudioTrack;
    let remoteVideoTrack;
    let isScreenSharing = false;
    let isRemoteSharing = false;
    let p2pReconnectTimeout;
    let dataChannel; // DataChannel se mantiene: hook para futuras integraciones

    // --- Referencias al DOM ---
    // Nota: pueden ser null si el script se ejecuta antes de renderizar el DOM.
    // En acciones posteriores siempre verificamos existencia (if (elem) ...).
    const localVideo = document.getElementById("localVideo");
    const remoteVideo = document.getElementById("remoteVideo");
    const statusEl = document.getElementById("status");
    const waitingMessage = document.getElementById("waitingMessage");

    // Botones de control
    const btnToggleMic = document.getElementById("btnToggleMic");
    const btnToggleCam = document.getElementById("btnToggleCam");
    const btnEndCall = document.getElementById("btnEndCall");
    const btnShareScreen = document.getElementById("btnShareScreen");
    const btnToggleFullscreen = document.getElementById("btnToggleFullscreen");
    const remoteVideoWrapper = document.getElementById("remoteVideoWrapper"); // Necesario para fullscreen

    // Chat DOM elements (se mantienen en DOM pero NO tendrán lógica interna aquí)
    const chatInput = document.getElementById("chatInput");
    const btnSendMessage = document.getElementById("btnSendMessage");
    const chatMessages = document.getElementById("chatMessages");

    // ICE servers
    const configuration = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

    // =========================================================
    // GESTOR DE WEBSOCKET ROBUSTO (CLASE)
    // =========================================================

    // --- CONSTANTES DE CONEXIÓN Y RECONEXIÓN ---
    const MAX_RECONNECT_ATTEMPTS = 15; // Límite de intentos de reconexión
    const INITIAL_RECONNECT_DELAY = 1000; // 1 segundo de retraso inicial
    const MAX_RECONNECT_DELAY = 30000; // Máximo 30 segundos de retraso

    // --- CONSTANTES DE HEARTBEAT ---
    const HEARTBEAT_INTERVAL = 30000; // Enviar un PING cada 30 segundos
    const HEARTBEAT_TIMEOUT = 5000;   // Esperar PONG por 5 segundos

    class TutoriaWebsocketManager {
        constructor(url, messageHandler) {
            this.url = url;
            this.messageHandler = messageHandler;

            this.socket = null;
            this.reconnectAttempts = 0;
            this.isConnected = false;
            this.isUserClosing = false;

            this.pingTimer = null;
            this.pongTimeout = null;
        }

        connect() {
            if (this.socket) {
                // Asegura que la conexión anterior se cierre antes de crear una nueva
                this.socket.onclose = null;
                this.socket.close();
            }

            console.log(`[WS] Intentando conectar a ${this.url}`);
            this.socket = new WebSocket(this.url);
            this.isUserClosing = false; // Reset al intentar conectar

            this.socket.onopen = this.onOpen.bind(this);
            this.socket.onmessage = this.onMessage.bind(this);
            this.socket.onclose = this.onClose.bind(this);
            this.socket.onerror = this.onError.bind(this);
        }

        onOpen() {
            console.log(`[WS] Conectado exitosamente. Intentos de reconexión: ${this.reconnectAttempts}`);
            this.isConnected = true;

            if (this.reconnectAttempts > 0) {
                // Notificar a la aplicación principal que se reanudó la conexión P2P
                this.messageHandler({ type: 'reconnect_success' });
            }

            this.reconnectAttempts = 0; // Resetear contador al tener éxito
            if (statusEl) statusEl.textContent = "WebSocket Conectado. Enviando join...";

            // Iniciar el Heartbeat
            this.startHeartbeat();

            // Enviar el mensaje de JOIN después de conectar/reconectar
            this.send({ type: "join", user_id: USER_ID, role: ROLE });
        }

        onClose(event) {
            this.isConnected = false;
            this.stopHeartbeat(); // Detener Heartbeat al cerrar

            if (this.isUserClosing) {
                console.log("[WS] Desconexión limpia iniciada por el usuario (Código 1000).");
                return;
            }

            console.warn(`[WS] Conexión cerrada. Código: ${event.code}.`);

            if (this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                this.reconnectAttempts++;

                // Fórmula de Exponential Backoff
                let delay = INITIAL_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts);
                delay = Math.min(delay, MAX_RECONNECT_DELAY);

                console.log(`[WS] Reintentando en ${delay / 1000}s (Intento #${this.reconnectAttempts})...`);
                if (statusEl) { statusEl.textContent = `Reconectando WebSocket... Intento #${this.reconnectAttempts} 🔄`; statusEl.style.color = "orange"; }

                setTimeout(() => {
                    this.connect();
                }, delay);
            } else {
                console.error("[WS] Límite de reconexión alcanzado. Conexión fallida permanente.");
                this.messageHandler({ type: 'connection_failed_permanent' });
            }
        }

        onError(error) {
            console.error("[WS] Error de WebSocket:", error);
        }

        // --- Heartbeat Logic ---
        startHeartbeat() {
            if (this.pingTimer) clearInterval(this.pingTimer);
            this.pingTimer = setInterval(() => {
                this.send({ type: 'ping' });
                if (this.pongTimeout) clearTimeout(this.pongTimeout);
                this.pongTimeout = setTimeout(() => {
                    // Si el PONG no llega a tiempo, forzar cierre para iniciar la reconexión
                    console.warn("[WS] Heartbeat fallido (no se recibió PONG). Forzando desconexión.");
                    // Forzar el cierre inicia el proceso de reconexión en onClose()
                    if (this.socket) this.socket.close();
                }, HEARTBEAT_TIMEOUT);
            }, HEARTBEAT_INTERVAL);
        }

        stopHeartbeat() {
            if (this.pingTimer) {
                clearInterval(this.pingTimer);
                this.pingTimer = null;
            }
            if (this.pongTimeout) {
                clearTimeout(this.pongTimeout);
                this.pongTimeout = null;
            }
        }

        onMessage(event) {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'pong') {
                    // Recibido el PONG, limpiar el timeout
                    clearTimeout(this.pongTimeout);
                    this.pongTimeout = null;
                    return;
                }

                // Reenvía todos los demás mensajes al manejador principal de la aplicación
                this.messageHandler(data);

            } catch (e) {
                console.error("[WS] Error al procesar mensaje JSON:", e);
            }
        }

        // --- Métodos Públicos ---
        close() {
            this.isUserClosing = true;
            this.stopHeartbeat();
            if (this.socket) {
                this.socket.close(1000, "User ended call"); // Cierre limpio
            }
        }

        send(data) {
            if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify(data));
            } else {
                console.warn(`[WS] Intento de envío fallido: WebSocket no está abierto. Mensaje: ${data.type}`);
            }
        }
    }

    // =========================================================
    // 1. INICIALIZACIÓN DE DISPOSITIVOS
    // =========================================================

    /**
     * Intenta obtener media de forma flexible, primero audio, luego video.
     */
    async function initMedia(timeoutMs = 5000) {
        console.log("LOG: Iniciando acceso flexible a media...");
        const newStream = new MediaStream();
        let audioReady = false;
        let videoReady = false;

        // Función helper para obtener media con timeout
        async function tryGetMedia(constraints) {
            try {
                return await Promise.race([
                    navigator.mediaDevices.getUserMedia(constraints),
                    new Promise((_, reject) => setTimeout(() => reject("timeout"), timeoutMs))
                ]);
            } catch (err) {
                console.error("Error: ", err);
            }
        }

        // --- 1. Micrófono ---
        const audioStream = await tryGetMedia({ audio: true, video: false });
        if (audioStream && audioStream.getAudioTracks().length > 0) {
            newStream.addTrack(audioStream.getAudioTracks()[0]);
            audioReady = true;
            console.log("LOG: Micrófono (Audio) obtenido OK.");
        } else {
            console.warn("LOG WARNING: No se pudo obtener micrófono.");
            if (btnToggleMic) {
                btnToggleMic.disabled = true;
                btnToggleMic.classList.replace('btn-light', 'btn-danger');
            }
        }

        // ... (código anterior)

        // --- 2. Cámara ---
        const videoResult = await tryGetMedia({ audio: false, video: true });
        let errorReason = null; // Variable para almacenar el objeto/razón del fallo

        if (videoResult instanceof MediaStream && videoResult.getVideoTracks().length > 0) {
            newStream.addTrack(videoResult.getVideoTracks()[0]);
            videoReady = true;
            console.log("LOG: Cámara (Video) obtenida OK.");
        } else {
            // 1. Determinar la razón del fallo
            if (videoResult && videoResult instanceof Error) {
                // La promesa falló, videoResult es el objeto Error nativo (NotAllowedError, NotFoundError, etc.)
                errorReason = videoResult;
            } else if (videoResult === 'timeout') {
                // La promesa se rechazó por timeout, enviamos un mensaje específico de error.
                errorReason = "Error: Timeout (Tiempos de espera agotados al obtener media)";
            } else {
                // Fallo genérico (ej: no hay tracks, pero no hubo error explícito)
                errorReason = "LOG WARNING: No se pudo obtener cámara. (Sin tracks o fallo genérico)";
            }

            // 2. Registrar el error en la consola
            if (errorReason instanceof Error) {
                // Muestra el objeto de Error nativo tal cual lo manda el navegador.
                console.error("LOG ERROR: Fallo al obtener cámara. Error nativo del navegador a continuación:", errorReason);
            } else {
                // Muestra el mensaje de timeout o fallo genérico.
                console.warn(errorReason);
            }

            // 3. Deshabilitar botón
            if (btnToggleCam) {
                btnToggleCam.disabled = true;
                // Asumiendo que 'btn-control' es la clase de estilo base
                btnToggleCam.classList.remove('btn-control');
                btnToggleCam.classList.add('btn-danger');
            }
        }

        // --- 3. Finalización ---
        if (audioReady || videoReady) {
            localStream = newStream;
            if (localVideo) localVideo.srcObject = localStream;
            console.log("LOG: Acceso a media OK. Tracks obtenidos:", localStream.getTracks().length);
            if (statusEl) { statusEl.textContent = "Media local lista. Conectando..."; statusEl.style.color = "blue"; }
        } else {
            localStream = null;
            console.warn("LOG WARNING: Ningún dispositivo de media disponible.");
            if (statusEl) { statusEl.textContent = "Conectando sin cámara ni micrófono…"; statusEl.style.color = "orange"; }
            if (btnToggleMic) btnToggleMic.disabled = true;
            if (btnToggleCam) btnToggleCam.disabled = true;
            if (btnShareScreen) btnShareScreen.disabled = true;
        }

        // HOOK: habilitar inputs de chat (se mantienen en DOM, pero no funcionales aquí).
        if (chatInput) chatInput.disabled = false;
        if (btnSendMessage) btnSendMessage.disabled = false;
    }

    // =========================================================
    // 2. LÓGICA DE CONEXIÓN WEBRTC (P2P)
    // =========================================================
    let audioSender;
    let videoSender;

    function createPeerConnection() {
        console.log("LOG: Creando nueva RTCPeerConnection.");

        if (peerConnection && peerConnection.connectionState !== "closed") {
            console.log("LOG: PeerConnection ya existe, abortando creación.");
            return;
        }
        if (peerConnection) peerConnection.close();

        peerConnection = new RTCPeerConnection(configuration);

        attachP2PUnloadGuard(peerConnection);

        // --- DataChannel Setup ---
        if (ROLE === "Tutor") {
            dataChannel = peerConnection.createDataChannel("chat");
            setupDataChannel(dataChannel);
        } else {
            peerConnection.ondatachannel = (event) => {
                dataChannel = event.channel;
                setupDataChannel(dataChannel);
            };
        }

        // =========================================================
        // MODIFICACIÓN CRÍTICA: Asegurar Transceptores Recvonly 🎧 📹
        // Esto garantiza que la oferta SDP siempre incluya m-lines para Audio y Video, 
        // permitiendo recibir media del par remoto incluso si la local falla.
        // =========================================================

        // Variables de verificación local
        const hasLocalAudio = localStream ? localStream.getAudioTracks().length > 0 : false;
        const hasLocalVideo = localStream ? localStream.getVideoTracks().length > 0 : false;

        if (!hasLocalAudio) {
            peerConnection.addTransceiver('audio', { direction: 'recvonly' });
            console.log("LOG: Transceptor de Audio añadido como recvonly (Micrófono local no disponible).");
        }

        if (!hasLocalVideo) {
            peerConnection.addTransceiver('video', { direction: 'recvonly' });
            console.log("LOG: Transceptor de Video añadido como recvonly (Cámara local no disponible).");
        }

        // 2. AÑADIR TRACKS LOCALES Y GUARDAR SENDERS
        // Si la media local existe, se añade aquí como 'sendrecv' o 'sendonly' por defecto.
        if (localStream && localStream.getTracks().length > 0) {
            localStream.getTracks().forEach(track => {
                // Nota: Solo añadimos el track si existe, si no existe ya hemos 
                // añadido el transceptor recvonly arriba.
                if (track.kind === 'video') {
                    videoSender = peerConnection.addTrack(track, localStream);
                    console.log("LOG: Video track añadido al PeerConnection.");
                } else if (track.kind === 'audio') {
                    audioSender = peerConnection.addTrack(track, localStream);
                    console.log("LOG: Audio track añadido al PeerConnection.");
                }
            });
        } else {
            console.log("LOG: localStream es nulo/vacío. Conexión P2P sin media inicial.");
        }

        // 3. Recibir tracks remotos (código existente)
        peerConnection.ontrack = e => {
            console.log("LOG: Track remoto recibido:", e.track.kind);

            // 1. Usa el stream que viene del evento (el método preferido)
            const incomingStream = e.streams ? e.streams[0] : remoteStream;

            // 2. Asigna el srcObject SÓLO UNA VEZ al elemento video remoto
            if (remoteVideo && remoteVideo.srcObject !== incomingStream) {
                remoteVideo.srcObject = incomingStream;
                console.log("LOG: srcObject remoto asignado o reasignado.");
                // OPTIONAL: Añadir un .play() catch para asegurar la reproducción.
                remoteVideo.play().catch(e => console.warn("Error al intentar auto-reproducir video remoto:", e));
            }

            // 3. Agrega el track al stream si el navegador no lo hizo
            if (!remoteVideo.srcObject.getTrackById(e.track.id)) {
                remoteStream.addTrack(e.track);
                console.log(`LOG: Track de ${e.track.kind} agregado al remoteStream.`);
            }

            // **********************************************
            // 4. ALMACENA REFERENCIAS
            // **********************************************
            if (e.track.kind === 'audio') {
                remoteAudioTrack = e.track;
            } else if (e.track.kind === 'video') {
                remoteVideoTrack = e.track;
            }

            e.track.onended = () => {
                console.log(`LOG: Track remoto de ${e.track.kind} finalizado.`);

                if (e.track.kind === 'video') {
                    remoteVideoTrack = null;
                    // Si el video se detiene, volvemos a mostrar el mensaje de espera
                    if (waitingMessage) {
                        waitingMessage.classList.remove("d-none");
                    }
                    // Importante: Si el audio sigue activo, debemos crear un nuevo MediaStream 
                    // solo con el audio para que el video player no se quede colgado.
                    if (remoteVideo && remoteAudioTrack) {
                        remoteVideo.srcObject = new MediaStream([remoteAudioTrack]);
                    } else if (remoteVideo) {
                        // Si no hay nada, limpiar el srcObject
                        remoteVideo.srcObject = null;
                    }
                } else if (e.track.kind === 'audio') {
                    remoteAudioTrack = null;
                }

                // Recomendación: Forzar renegociación para limpiar las m-lines inactivas
                if (peerConnection.connectionState === 'connected' && ROLE === 'Tutor') {
                    console.log("LOG: Track remoto finalizado. Forzando renegociación.");
                    peerConnection.dispatchEvent(new Event('negotiationneeded'));
                }
            };

            // 5. Oculta el mensaje de espera solo cuando llegue el VIDEO.
            if (remoteVideoTrack && waitingMessage) {
                waitingMessage.classList.add("d-none");
            }
        };

        // 4. ICE y Negociación (código existente)
        peerConnection.onicecandidate = event => {
            if (event.candidate && wsManager && wsManager.isConnected) {
                wsManager.send({ type: "ice-candidate", candidate: event.candidate });
            }
        };

        let isNegotiating = false;

        peerConnection.onnegotiationneeded = async () => {
            console.log("LOG: Negociación necesaria. Intentando enviar oferta...");

            if (isNegotiating) {
                console.log("LOG: Negociación ya en curso, ignorando solicitud.");
                return;
            }

            if (ROLE === "Tutor" && wsManager && wsManager.isConnected) {
                isNegotiating = true;

                try {
                    const offer = await peerConnection.createOffer({ iceRestart: true });
                    await peerConnection.setLocalDescription(offer);
                    wsManager.send({ type: "offer", sdp: offer });
                    console.log("LOG: Oferta de renegociación enviada.");
                } catch (err) {
                    console.error("LOG ERROR: Error al crear oferta en negociación:", err);
                } finally {
                    isNegotiating = false;
                }
            }
        };
        // 5. Monitoreo de estado (código existente)
        peerConnection.onconnectionstatechange = () => {
            const state = peerConnection.connectionState;
            console.log("LOG: PeerConnection State:", state);

            if (state === "disconnected" || state === "failed") {
                if (statusEl) { statusEl.textContent = "Desconexión P2P. Reintentando... 🔄"; statusEl.style.color = "orange"; }
                if (ROLE === "Tutor" && wsManager && wsManager.isConnected) {
                    if (p2pReconnectTimeout) clearTimeout(p2pReconnectTimeout);
                    p2pReconnectTimeout = setTimeout(() => {
                        console.log("LOG: Forzando renegociación ICE...");
                        try {
                            if (peerConnection && peerConnection.signalingState !== 'closed') {
                                peerConnection.restartIce();
                            }
                        } catch (e) {
                            console.warn("Error al forzar restartIce:", e);
                        }
                    }, 5000);
                }
            } else if (state === "connected") {
                if (statusEl) { statusEl.textContent = "Conectado ✅"; statusEl.style.color = "green"; }
                if (p2pReconnectTimeout) clearTimeout(p2pReconnectTimeout);
            }
        };
    }

    // =========================================================
    // 3. LÓGICA DE DATA CHANNEL (NO-CHAT / HOOKS)
    // =========================================================

    function setupDataChannel(channel) {
        dataChannel = channel;
        console.log("LOG: DataChannel establecido (sin lógica de chat por defecto).");

        dataChannel.onopen = () => {
            console.log("LOG: DataChannel abierto.");
            // HOOK: si quieres notificar UI sobre el canal abierto, implementa:
            // window.onDataChannelOpen && window.onDataChannelOpen();
        };

        dataChannel.onclose = () => {
            console.warn("LOG WARNING: DataChannel cerrado.");
            // HOOK: window.onDataChannelClose && window.onDataChannelClose();
        };

        // Mensajes entrantes por DataChannel: **no procesamos como chat interno**.
        // Devolveremos el payload a un handler global si existe (para integraciones futuras).
        dataChannel.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                console.log("LOG: Mensaje recibido por DataChannel (payload):", payload);
                // HOOK: si implementas una función global para manejar mensajes DC:
                if (typeof window.handleDataChannelMessage === 'function') {
                    window.handleDataChannelMessage(payload);
                }
                // No mostramos mensajes en UI aquí (chat se manejará por el chat general).
            } catch (err) {
                console.warn("LOG WARNING: Mensaje DC no JSON o error al parsear:", err);
            }
        };
    }

    // Fullscreen helper (sin cambios)
    function toggleFullscreen() {
        const isFullscreen = document.fullscreenElement;
        const icon = btnToggleFullscreen ? btnToggleFullscreen.querySelector('i') : null;

        if (!isFullscreen) {
            if (remoteVideoWrapper && remoteVideoWrapper.requestFullscreen) {
                remoteVideoWrapper.requestFullscreen();
            } else if (remoteVideoWrapper && remoteVideoWrapper.webkitRequestFullscreen) { /* Safari */
                remoteVideoWrapper.webkitRequestFullscreen();
            } else if (remoteVideoWrapper && remoteVideoWrapper.msRequestFullscreen) { /* IE11 */
                remoteVideoWrapper.msRequestFullscreen();
            }
            if (icon) { icon.classList.remove('bi-arrows-fullscreen'); icon.classList.add('bi-fullscreen-exit'); }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) { /* Safari */
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) { /* IE11 */
                document.msExitFullscreen();
            }
            if (icon) { icon.classList.remove('bi-fullscreen-exit'); icon.classList.add('bi-arrows-fullscreen'); }
        }
    }

    // Placeholder no-op appendMessage (mantener hook; NO muestra nada)
    function appendMessage(/* message, sender */) {
        // NO-OP: el chat se gestiona con el chat general externo.
        // Si quieres ver logs para debugging, descomenta:
        // console.log("appendMessage() llamado pero chat local está desactivado.");
    }

    // sendMessage ahora es un stub que muestra cómo conectar el chat general
    function sendMessage() {
        // NO-OP: aquí no enviamos al DataChannel como chat interno.
        // Si quieres que el botón de enviar invoque el chat general, implementa:
        // window.sendChatGeneral && window.sendChatGeneral(chatInput.value);
        console.warn("sendMessage() llamado pero chat local está desactivado. Usa tu chat general.");
    }

    // =========================================================
    // 4. SEÑALIZACIÓN (WEBSOCKETS) Y AUXILIARES
    // =========================================================

    async function handleWebsocketMessage(data) {
        console.log("LOG: Mensaje WS recibido:", data.type);

        try {
            switch (data.type) {
                case "reset_connection":
                    console.log("LOG: Usuario remoto se reconectó, reiniciando PeerConnection.");
                    if (peerConnection) peerConnection.close();
                    createPeerConnection();
                    // Notifica al usuario que recargó para que haga offer
                    if (wsManager && wsManager.isConnected) wsManager.send({ type: "reconnect_success" });
                    break;

                case "reconnect_success":
                    console.log("LOG: Reconexión de WS exitosa. Forzando renegociación P2P.");
                    if (peerConnection && peerConnection.connectionState !== "closed" && ROLE === "Tutor") {
                        try {
                            await peerConnection.setLocalDescription(
                                await peerConnection.createOffer({ iceRestart: true })
                            );
                            if (wsManager && wsManager.isConnected) wsManager.send({ type: "offer", sdp: peerConnection.localDescription.sdp });
                        } catch (err) {
                            console.error("Error forzando renegociación:", err);
                        }
                    }
                    break;

                case "connection_failed_permanent":
                    endCall(true);
                    if (statusEl) { statusEl.textContent = "Error: Conexión perdida permanentemente. 🛑"; statusEl.style.color = "red"; }
                    break;

                case "user_joined":
                    if (!peerConnection || peerConnection.connectionState === "closed") {
                        createPeerConnection();
                        if (ROLE === "Tutor") {
                            console.log("LOG: Tutor enviando Offer inicial.");
                            try {
                                const offer = await peerConnection.createOffer();
                                await peerConnection.setLocalDescription(offer);
                                if (wsManager && wsManager.isConnected) wsManager.send({ type: "offer", sdp: offer.sdp });
                            } catch (err) {
                                console.error("Error creando offer al unirse usuario:", err);
                            }
                        }
                    }
                    break;

                case "offer":
                    console.log("LOG: Recibida Offer. Enviando Answer.");
                    if (!peerConnection || peerConnection.connectionState === "closed") createPeerConnection();

                    try {
                        await peerConnection.setRemoteDescription({ type: "offer", sdp: data.sdp });
                        await flushPendingIceCandidates();
                        const answer = await peerConnection.createAnswer();
                        await peerConnection.setLocalDescription(answer);
                        if (wsManager && wsManager.isConnected) wsManager.send({ type: "answer", sdp: answer.sdp });
                    } catch (err) {
                        console.error("Error procesando offer:", err);
                    }
                    break;

                case "answer":
                    console.log("LOG: Recibida Answer.");
                    if (!peerConnection || peerConnection.connectionState === "closed") createPeerConnection();

                    try {
                        await peerConnection.setRemoteDescription({ type: "answer", sdp: data.sdp });
                        await flushPendingIceCandidates();
                    } catch (err) {
                        console.error("Error procesando answer:", err);
                    }
                    break;

                case "ice-candidate":
                    if (!data.candidate) break;
                    if (!peerConnection || peerConnection.remoteDescription === null) {
                        pendingIceCandidates.push(data.candidate);
                    } else {
                        try {
                            await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
                        } catch (err) {
                            console.warn("LOG WARNING: Error al añadir ICE candidate:", err);
                        }
                    }
                    break;

                case "screen_share_start":
                    if (data.user_id !== USER_ID) {
                        isRemoteSharing = true;
                        if (statusEl) { statusEl.textContent = "El otro usuario está compartiendo su pantalla. 🖥️"; statusEl.style.color = "blue"; }
                        if (btnShareScreen) btnShareScreen.disabled = true;
                    }
                    break;

                case "screen_share_stop":
                    if (data.user_id !== USER_ID) {
                        isRemoteSharing = false;
                        if (statusEl) { statusEl.textContent = "Conectado ✅"; statusEl.style.color = "green"; }
                        if (btnShareScreen) btnShareScreen.disabled = false;
                    }
                    break;

                case "user_left":
                    console.log("LOG: Usuario remoto salió.");
                    if (remoteVideo) remoteVideo.srcObject = null;
                    remoteVideoTrack = null;
                    remoteAudioTrack = null;
                    if (statusEl) { statusEl.textContent = "El otro usuario salió ❌"; statusEl.style.color = "red"; }
                    if (waitingMessage) waitingMessage.classList.remove("d-none");
                    break;

                case "evaluacion_publicada":
                    if (typeof showResponseButtonDynamically === 'function' && ROLE === 'Estudiante') {
                        showResponseButtonDynamically(data.evaluacion_id);
                    }
                    break;

                // Nota: No procesamos 'chat_message' localmente; el chat general debe usar su propio WS/consumer.
            }
        } catch (err) {
            console.error("LOG ERROR: Error manejando mensaje WS:", err, data);
        }
    }

    function enableUnloadProtection() {
        window.onbeforeunload = (e) => {
            e.preventDefault();
            e.returnValue = "";
        };
    }

    function disableUnloadProtection() {
        window.onbeforeunload = null;
    }

    // Activar / desactivar según estado real del WebRTC
    function attachP2PUnloadGuard(pc) {
        pc.addEventListener("connectionstatechange", () => {
            const state = pc.connectionState;
            console.log("LOG: Estado P2P:", state);

            if (state === "connected" || state === "connecting") {
                enableUnloadProtection();
            } else {
                disableUnloadProtection();
            }
        });
    }

    /**
     * Inicializa el Gestor de WebSocket y conecta.
     */
    function connectWebSocket() {
        wsManager = new TutoriaWebsocketManager(wsPath, handleWebsocketMessage);
        wsManager.connect();
    }

    async function flushPendingIceCandidates() {
        if (!peerConnection || !pendingIceCandidates.length) return;
        console.log(`LOG: Añadiendo ${pendingIceCandidates.length} ICE candidates pendientes.`);
        while (pendingIceCandidates.length) {
            const candidate = pendingIceCandidates.shift();
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
            } catch (err) {
                console.warn("LOG WARNING: Error al añadir pending candidate:", err, candidate);
            }
        }
    }

    // =========================================================
    // 5. LÓGICA DE CONTROLES
    // =========================================================
    let currentAudioEnabled = true;
    let currentVideoEnabled = true;

    function toggleTrack(track, button, isAudio) {
        if (!track) return;
        track.enabled = !track.enabled;
        let enabled = track.enabled;
        const icon = button ? button.querySelector('i') : null;

        if (isAudio) {
            currentAudioEnabled = enabled;
            if (icon) { icon.classList.toggle('bi-mic-fill', enabled); icon.classList.toggle('bi-mic-mute-fill', !enabled); }
        } else {
            currentVideoEnabled = enabled;
            if (icon) { icon.classList.toggle('bi-camera-video-fill', enabled); icon.classList.toggle('bi-camera-video-off-fill', !enabled); }
        }

        if (button) {
            button.classList.toggle('btn-light', enabled);
            button.classList.toggle('btn-danger', !enabled);
            button.title = enabled ? (isAudio ? 'Silenciar' : 'Cámara On/Off') : (isAudio ? 'Activar Mic' : 'Cámara Off/On');
        }
    }

    function toggleMic() {
        const audioTrack = localStream ? localStream.getAudioTracks()[0] : null;
        toggleTrack(audioTrack, btnToggleMic, true);
        console.log(`LOG: Micrófono toggled: ${currentAudioEnabled}`);
    }

    function toggleCam() {
        const videoTrack = localStream ? localStream.getVideoTracks()[0] : null;
        toggleTrack(videoTrack, btnToggleCam, false);
        console.log(`LOG: Cámara toggled: ${currentVideoEnabled}`);
    }

    async function startScreenSharing() {
        if (isScreenSharing) return;

        if (isRemoteSharing) {
            console.warn("LOG WARNING: El usuario remoto ya está compartiendo la pantalla. Espere.");
            if (statusEl) { statusEl.textContent = "El otro usuario está compartiendo. Espera tu turno."; statusEl.style.color = "red"; }
            setTimeout(() => {
                if (isRemoteSharing) {
                    if (statusEl) { statusEl.textContent = "El otro usuario está compartiendo su pantalla. 🖥️"; statusEl.style.color = "blue"; }
                } else {
                    if (statusEl) { statusEl.textContent = "Conectado ✅"; statusEl.style.color = "green"; }
                }
            }, 5000);
            return;
        }

        console.log("LOG: Iniciando Screen Sharing...");
        try {
            screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: true
            });
            isScreenSharing = true;

            if (wsManager && wsManager.isConnected) wsManager.send({ type: "screen_share_start", user_id: USER_ID });

            const screenVideoTrack = screenStream.getVideoTracks()[0];
            const screenAudioTrack = screenStream.getAudioTracks()[0]; // Puede ser undefined

            if (videoSender) {
                try { await videoSender.replaceTrack(screenVideoTrack); } catch (e) { console.warn("replaceTrack video failed:", e); }
            } else if (peerConnection && screenVideoTrack) {
                videoSender = peerConnection.addTrack(screenVideoTrack, screenStream);
            }

            if (screenAudioTrack) {
                if (audioSender) {
                    try { await audioSender.replaceTrack(screenAudioTrack); } catch (e) { console.warn("replaceTrack audio failed:", e); }
                } else if (peerConnection) {
                    audioSender = peerConnection.addTrack(screenAudioTrack, screenStream);
                }
            } else if (audioSender) {
                try { await audioSender.replaceTrack(null); } catch (e) { console.warn("replaceTrack(null) no soportado:", e); }
            }

            if (localVideo) localVideo.srcObject = screenStream;
            if (btnShareScreen) { btnShareScreen.classList.remove('btn-secondary'); btnShareScreen.classList.add('btn-warning'); btnShareScreen.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i> Detener'; }

            if (screenStream.getVideoTracks()[0]) screenStream.getVideoTracks()[0].onended = stopScreenSharing;

        } catch (err) {
            console.error("LOG ERROR: Fallo al iniciar Screen Sharing:", err);
            isScreenSharing = false;
        }
    }

    async function stopScreenSharing() {
        if (!isScreenSharing) return;

        if (wsManager && wsManager.isConnected) wsManager.send({ type: "screen_share_stop", user_id: USER_ID });
        console.log("LOG: Enviado screen_share_stop al servidor.");

        if (screenStream) {
            screenStream.getTracks().forEach(track => track.stop());
            screenStream = null;
        }
        isScreenSharing = false;

        const originalVideoTrack = localStream ? localStream.getVideoTracks()[0] : null;
        const originalAudioTrack = localStream ? localStream.getAudioTracks()[0] : null;

        if (videoSender && originalVideoTrack) {
            try { await videoSender.replaceTrack(originalVideoTrack); } catch (e) { console.warn("replaceTrack original video failed:", e); }
            if (originalVideoTrack) originalVideoTrack.enabled = currentVideoEnabled;
        } else if (videoSender) {
            try { await videoSender.replaceTrack(null); } catch (e) { console.warn("replaceTrack(null) video failed:", e); }
        }

        if (audioSender && originalAudioTrack) {
            try { await audioSender.replaceTrack(originalAudioTrack); } catch (e) { console.warn("replaceTrack original audio failed:", e); }
            if (originalAudioTrack) originalAudioTrack.enabled = currentAudioEnabled;
        } else if (audioSender) {
            try { await audioSender.replaceTrack(null); } catch (e) { console.warn("replaceTrack(null) audio failed:", e); }
        }

        if (localVideo) localVideo.srcObject = localStream;

        if (btnShareScreen) { btnShareScreen.classList.remove('btn-warning'); btnShareScreen.classList.add('btn-secondary'); btnShareScreen.innerHTML = '<i class="bi bi-display-fill me-1"></i> Compartir'; }
    }

    function endCall(isExternalFailure = false) {
        console.log(`LOG: Finalizando la llamada (Fallo externo: ${isExternalFailure})...`);

        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
        if (screenStream) {
            screenStream.getTracks().forEach(track => track.stop());
            screenStream = null;
        }

        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
        }

        if (wsManager) {
            wsManager.close();
        }

        if (localVideo) localVideo.srcObject = null;
        if (remoteVideo) remoteVideo.srcObject = null;
        if (!isExternalFailure && statusEl) { statusEl.textContent = "Llamada finalizada 🛑"; statusEl.style.color = "red"; }

        if (btnEndCall) btnEndCall.disabled = true;
        if (btnToggleCam) btnToggleCam.disabled = true;
        if (btnToggleMic) btnToggleMic.disabled = true;
        if (btnShareScreen) btnShareScreen.disabled = true;
    }

    // =========================================================
    // 6. LISTENERS DE BOTONES E INICIO
    // =========================================================
    console.log("LOG: DOMContentLoaded. Iniciando flujo de aplicación.");

    // Asignar referencias a botones de acciones si existen (local scope)



    // --- 6.1. Controles Básicos ---
    if (btnToggleMic) btnToggleMic.addEventListener('click', toggleMic);
    if (btnToggleCam) btnToggleCam.addEventListener('click', toggleCam);
    if (btnEndCall) btnEndCall.addEventListener('click', endCall);
    if (btnToggleFullscreen) btnToggleFullscreen.addEventListener('click', toggleFullscreen);
    if (btnShareScreen) btnShareScreen.addEventListener('click', () => {
        if (isScreenSharing) {
            stopScreenSharing();
        } else {
            startScreenSharing();
        }
    });

    // --- 6.5. Inicio de WebRTC ---
    initMedia().then(connectWebSocket);


    // ==========================
    // 💬 CHAT GENERAL
    // ==========================
    // Verificar que chat.js cargó el módulo
    if (window.ChatModule) {

        // Obtener la conversación actual o la primera
        let chatDefault =
            document.querySelector(".conversation-item.active") ||
            document.querySelector(".conversation-item");

        if (chatDefault) {
            console.log("💬 Abriendo chat general desde videollamada...");
            window.ChatModule.openChat(chatDefault);
        } else {
            console.warn("⚠️ No hay conversaciones disponibles para el chat.");
        }

    } else {
        console.warn("⚠️ ChatModule no está disponible — ¿cargaste chat.js?");
    }

    console.log("✅ Chat general conectado a la UI de videollamada");


});



