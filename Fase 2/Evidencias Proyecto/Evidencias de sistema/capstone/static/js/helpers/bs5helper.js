// bs5helpers.js
window.BS5Helper = {
  // ────────── TOASTS ──────────
  Toast: {
    mostrar: function ({
      mensaje = "",
      tipo = "success",       // info, success, warning, danger
      duracion = 8000,        // duración en ms
      posicion = "top-end"    // top-start, top-end, bottom-start, bottom-end
    } = {}) {
      // Crear contenedor de toast si no existe
      let contenedor = document.getElementById("bs5-toast-container");
      if (!contenedor) {
        contenedor = document.createElement("div");
        contenedor.id = "bs5-toast-container";
        contenedor.style.position = "fixed";
        contenedor.style.zIndex = 1100;
        contenedor.style.top = posicion.includes("top") ? "1.5rem" : "";
        contenedor.style.bottom = posicion.includes("bottom") ? "1.5rem" : "";
        contenedor.style.left = posicion.includes("start") ? "1rem" : "";
        contenedor.style.right = posicion.includes("end") ? "1rem" : "";
        contenedor.style.display = "flex";
        contenedor.style.flexDirection = "column";
        contenedor.style.gap = "0.5rem";
        document.body.appendChild(contenedor);
      }

      // Crear toast
      const toastEl = document.createElement("div");
      toastEl.className = `toast align-items-center text-white bg-${tipo} border-0`;
      toastEl.setAttribute("role", "alert");
      toastEl.setAttribute("aria-live", "assertive");
      toastEl.setAttribute("aria-atomic", "true");
      toastEl.innerHTML = `
        <div class="d-flex">
          <div class="toast-body">${mensaje}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      `;

      contenedor.appendChild(toastEl);

      const toast = new bootstrap.Toast(toastEl, { delay: duracion });
      toast.show();

      toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
    }
  },

  // ────────── MODALS ──────────
  Modal: {
    alerta: function ({
      titulo = "Aviso",
      mensaje = "",
      tipo = "info", // info, success, warning, danger
      texto = "Aceptar",
      url = null
    } = {}) {

      return new Promise((resolve) => {

        // Crear modal si no existe
        let modalEl = document.getElementById("bs5-helper-alerta");
        if (!modalEl) {
          modalEl = document.createElement("div");
          modalEl.id = "bs5-helper-alerta";
          modalEl.className = "modal fade";
          modalEl.tabIndex = -1;
          document.body.appendChild(modalEl);
        }

        modalEl.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content text-center">

          <div class="modal-header justify-content-center border-0">
            <h5 class="modal-title">${titulo}</h5>
          </div>

          <div class="modal-body">
            <div class="fs-1 mb-3">
              ${tipo === "success" ? '<i class="bi bi-check-circle-fill text-success"></i>' :
            tipo === "danger" ? '<i class="bi bi-x-circle-fill text-danger"></i>' :
              tipo === "warning" ? '<i class="bi bi-exclamation-triangle-fill text-warning"></i>' :
                '<i class="bi bi-info-circle text-info"></i>'}
            </div>
            <p class="fs-5">${mensaje}</p>
          </div>

          <div class="modal-footer justify-content-center border-0">
            <button id="btn-alerta-ok" type="button" class="btn btn-primary">${texto}</button>
          </div>

        </div>
      </div>
    `;

        const bsModal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
        bsModal.show();

        // Acción botón aceptar
        modalEl.querySelector("#btn-alerta-ok").addEventListener("click", () => {
          bsModal.hide();
          resolve(true);
        });

        // Si se cierra → redirigir si corresponde
        modalEl.addEventListener("hidden.bs.modal", () => {
          if (url) window.location.href = url;
        }, { once: true });

      });
    },

    wait: function ({
      mensaje = "Cargando...",
      id = "modal-espera",
      cancelable = false,          // Nuevo: si true agrega botón Cancelar
      onCancel = null              // Función que se ejecuta al cancelar
    } = {}) {
      // Evitar duplicados
      if (document.getElementById(id)) return;

      // Botón de cancelar opcional
      const cancelButtonHtml = cancelable
        ? `<button type="button" class="btn btn-danger mt-3" id="${id}-cancel-btn">Cancelar</button>`
        : "";

      const modalHtml = `
        <div class="modal fade" id="${id}" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content text-center">
              <div class="modal-body">
                <p class="fs-5">${mensaje}</p>
                <div class="spinner-border text-primary mt-3" role="status">
                  <span class="visually-hidden">Cargando...</span>
                </div>
                <div class="mt-3">
                  ${cancelButtonHtml}
                </div>
              </div>
            </div>
          </div>
        </div>
    `;
      document.body.insertAdjacentHTML("beforeend", modalHtml);

      const modalEl = document.getElementById(id);
      const modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: false });
      modal.show();

      // Si hay botón cancelar, agregar evento
      if (cancelable && onCancel) {
        const btn = document.getElementById(`${id}-cancel-btn`);
        btn.addEventListener("click", () => {
          onCancel();     // Ejecutar función de cancelación
          modal.hide();   // Cerrar modal
        });
      }

      return modal; // Retorna la instancia para poder cerrarla más tarde
    },


    close: function (id = "modal-espera") {
      const modalEl = document.getElementById(id);
      if (!modalEl) return;

      // Si algún elemento dentro del modal tiene focus, lo removemos
      if (modalEl.contains(document.activeElement)) {
        document.activeElement.blur(); // Quita focus del elemento activo
        // O alternativamente mover focus al body
        // document.body.focus();
      }

      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();

      modalEl.addEventListener("hidden.bs.modal", () => modalEl.remove());
    },


    modalIcono: function ({ titulo = "Aviso", mensaje = "", tipo = "info", duracion = 3000, redirigiendo = 0 } = {}) {
      return new Promise((resolve) => {
        // Crear modal si no existe
        let modalEl = document.getElementById("bs5-helper-modal");
        if (!modalEl) {
          modalEl = document.createElement("div");
          modalEl.id = "bs5-helper-modal";
          modalEl.className = "modal fade";
          modalEl.tabIndex = -1;
          document.body.appendChild(modalEl);
        }

        modalEl.innerHTML = `
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content text-center">
              <div class="modal-header justify-content-center border-0">
                <h5 class="modal-title">${titulo}</h5>
              </div>
              <div class="modal-body">
                <div class="fs-1 mb-3">
                  ${tipo === "success" ? '<i class="bi bi-check-circle-fill text-success"></i>' :
            tipo === "danger" ? '<i class="bi bi-x-circle-fill text-danger"></i>' :
              tipo === "warning" ? '<i class="bi bi-exclamation-triangle-fill text-warning"></i>' :
                '<i class="bi bi-info-circle-fill text-info"></i>'
          }
                </div>
                <p class="fs-5">${mensaje}</p>
                ${redirigiendo === 0
            ? '<button type="button" class="btn btn-primary mt-3" data-bs-dismiss="modal">Cerrar</button>'
            : redirigiendo === 1
              ? '<div class="spinner-border text-primary mt-3" role="status"><span class="visually-hidden">Cargando...</span></div>'
              : ''
          }
              </div>
            </div>
          </div>
        `;

        const bsModal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
        bsModal.show();

        if (redirigiendo === 1) {
          setTimeout(() => {
            bsModal.hide();
            resolve();
          }, duracion);
        } else {
          modalEl.addEventListener("hidden.bs.modal", () => resolve(), { once: true });
        }
      });
    },

    confirmacion: function ({
      titulo = "Confirmar acción",
      mensaje = "¿Estás seguro?",
      tipo = "warning",
      textoSi = "Sí",
      textoNo = "No",
      eliminar = 0
    } = {}) {
      return new Promise((resolve) => {
        // Crear modal si no existe
        let modalEl = document.getElementById("bs5-helper-confirmacion");
        if (!modalEl) {
          modalEl = document.createElement("div");
          modalEl.id = "bs5-helper-confirmacion";
          modalEl.className = "modal fade";
          modalEl.tabIndex = -1;
          document.body.appendChild(modalEl);
        }

        modalEl.innerHTML = `
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content text-center">
              <div class="modal-header justify-content-center border-0">
                <h5 class="modal-title">${titulo}</h5>
              </div>
              <div class="modal-body">
                <div class="fs-1 mb-3">
                  ${tipo === "success" ? '<i class="bi bi-check-circle-fill text-success"></i>' :
            tipo === "danger" ? '<i class="bi bi-x-circle-fill text-danger"></i>' :
              tipo === "warning" ? '<i class="bi bi-exclamation-triangle-fill text-warning"></i>' :
                '<i class="bi bi-info-circle-fill text-info"></i>'
          }
                </div>
                <p class="fs-5">${mensaje}</p>
              </div>
              <div class="modal-footer justify-content-center border-0">
                <button type="button" class="btn btn-secondary" id="btn-no">${textoNo}</button>
                ${eliminar === 0
            ? `<button type="button" class="btn btn-primary" id="btn-si">${textoSi}</button>`
            : `<button type="button" class="btn btn-danger" id="btn-si">${textoSi}</button>`
          }
              </div>
            </div>
          </div>
        `;

        const bsModal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
        bsModal.show();

        // Manejar botones
        modalEl.querySelector("#btn-si").addEventListener("click", () => {
          bsModal.hide();
          resolve(true);
        });

        modalEl.querySelector("#btn-no").addEventListener("click", () => {
          bsModal.hide();
          resolve(false);
        });

        // Resolver en false si se cierra con ESC o clic fuera
        modalEl.addEventListener("hidden.bs.modal", () => resolve(false), { once: true });
      });
    },

    custom: function ({
      titulo = "",
      html = "",
      textoSi = "Aceptar",
      textoNo = "Cancelar",
      size = "modal-md",
      onOpen = null
    } = {}) {

      return new Promise((resolve) => {

        // Crear modal dinámico
        const modalId = "modalCustom_" + Date.now();
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog ${size}">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${titulo}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${html}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary btnCancel">${textoNo}</button>
                            <button type="button" class="btn btn-primary btnOk">${textoSi}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML("beforeend", modalHtml);

        const modalEl = document.getElementById(modalId);
        const bsModal = new bootstrap.Modal(modalEl);

        // Botones
        const btnOk = modalEl.querySelector(".btnOk");
        const btnCancel = modalEl.querySelector(".btnCancel");

        btnCancel.addEventListener("click", () => {
          bsModal.hide();
          resolve(null);
        });

        btnOk.addEventListener("click", () => {
          bsModal.hide();
          resolve("ok");
        });

        // onOpen callback
        if (typeof onOpen === "function") {
          modalEl.addEventListener("shown.bs.modal", () => {
            onOpen(modalEl);
          });
        }

        // Eliminar el modal al cerrarse
        modalEl.addEventListener("hidden.bs.modal", () => {
          modalEl.remove();
        });

        bsModal.show();
      });
    },

    PDFViewer: function ({ url = "", titulo = "Vista previa del archivo", descargar = false } = {}) {
      if (!url) {
        console.error("BS5Helper.PDFViewer: falta el parámetro 'url'");
        return;
      }

      // Crear modal si no existe
      let modalEl = document.getElementById("bs5-pdf-viewer");
      if (!modalEl) {
        modalEl = document.createElement("div");
        modalEl.id = "bs5-pdf-viewer";
        modalEl.className = "modal fade";
        modalEl.tabIndex = -1;
        modalEl.innerHTML = `
      <div class="modal-dialog modal-xl modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="pdfViewerTitle">${titulo}</h5>
            <div class="d-flex align-items-center gap-2">
              <a id="btnDownload" class="btn btn-sm btn-outline-primary d-none" target="_blank" title="Descargar PDF">
                <i class="bi bi-download"></i>
              </a>
              <button id="btnFullscreen" class="btn btn-sm btn-outline-secondary" title="Pantalla completa">
                <i class="bi bi-arrows-fullscreen"></i>
              </button>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
            </div>
          </div>
          <div class="modal-body p-0" style="height: 80vh; background: #f8f9fa;">
            <iframe id="pdfFrame"
                    width="100%"
                    height="100%"
                    frameborder="0"
                    sandbox="allow-same-origin allow-scripts"
                    allow="clipboard-read; clipboard-write"
                    style="border: none;"></iframe>
          </div>
        </div>
      </div>
    `;
        document.body.appendChild(modalEl);
      }

      const pdfFrame = modalEl.querySelector("#pdfFrame");
      const btnFullscreen = modalEl.querySelector("#btnFullscreen");
      const btnDownload = modalEl.querySelector("#btnDownload");
      const titleEl = modalEl.querySelector("#pdfViewerTitle");

      // Actualizar título
      titleEl.textContent = titulo;

      // Mostrar PDF con Google Docs Viewer (evita descarga)
      pdfFrame.src = `https://docs.google.com/gview?url=${encodeURIComponent(url)}&embedded=true`;

      // Si está habilitada la descarga, mostrar botón
      if (descargar) {
        btnDownload.classList.remove("d-none");
        btnDownload.href = url;
      } else {
        btnDownload.classList.add("d-none");
      }

      // Pantalla completa
      btnFullscreen.onclick = () => {
        if (pdfFrame.requestFullscreen) pdfFrame.requestFullscreen();
        else if (pdfFrame.webkitRequestFullscreen) pdfFrame.webkitRequestFullscreen();
        else if (pdfFrame.mozRequestFullScreen) pdfFrame.mozRequestFullScreen();
        else if (pdfFrame.msRequestFullscreen) pdfFrame.msRequestFullscreen();
      };

      // Limpiar iframe al cerrar
      modalEl.addEventListener("hidden.bs.modal", () => {
        pdfFrame.src = "";
        if (document.fullscreenElement) document.exitFullscreen();
      }, { once: true });

      // Mostrar modal
      const bsModal = new bootstrap.Modal(modalEl, { backdrop: "static", keyboard: true });
      bsModal.show();
    }

  }
};
