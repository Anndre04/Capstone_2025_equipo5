document.addEventListener('DOMContentLoaded', function () {
    console.log('✅ Archivo tutoria.js cargado correctamente');

    // SECCIÓN: ANUNCIOTUTOR.HTML
    const tutorCards = document.querySelectorAll('.card');
    tutorCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transition = 'all 0.3s ease';
        });
    });

    // SECCIÓN: GESTORTUTORIAS.HTML (Tempus Dominus)
    const datetimePickerElement = document.getElementById("datetimepicker-fechagestortutoria");
    if (datetimePickerElement && typeof tempusDominus !== 'undefined') {
        const picker = new tempusDominus.TempusDominus(
            datetimePickerElement,
            {
                display: {
                    theme: "light",
                    viewMode: "calendar",
                    components: {
                        calendar: true,
                        date: true,
                        month: true,
                        year: true,
                        decades: true,
                        clock: false, // ❌ sin hora
                    },
                    icons: {
                        previous: "bi bi-chevron-left",
                        next: "bi bi-chevron-right",
                    },
                },
                localization: {
                    locale: "es-ES",
                    startOfTheWeek: 1,
                    format: "yyyy-MM-dd",
                    dayViewHeaderFormat: { month: "long", year: "numeric" },
                },
                restrictions: {
                    maxDate: new Date(), // ⛔ no deja elegir fechas futuras
                },
                useCurrent: false,
            }
        );

        const inputFecha = document.getElementById('fechagestortutoria');
        if (inputFecha) {
            inputFecha.addEventListener('focus', () => picker.show());
            inputFecha.addEventListener('click', () => picker.show());

            // 🔧 Al seleccionar una fecha, la formateamos sin hora
            document
                .getElementById("datetimepicker-fechagestortutoria")
                .addEventListener("change.td", (e) => {
                    if (e.detail?.date) {
                        const date = e.detail.date;
                        const year = date.year;
                        const month = String(date.month + 1).padStart(2, "0");
                        const day = String(date.date).padStart(2, "0");
                        inputFecha.value = `${year}-${month}-${day}`;
                    }
                });
        }
    }


    // ------------------------------------
    // SECCIÓN: MISTUTORIASPROF.HTML
    // ------------------------------------

    // Inicialización de Tooltips (se mantiene)
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(el => new bootstrap.Tooltip(el));
    }

    // Estructura de datos (se mantiene)
    const diasData = [
        { nombre: 'Lunes', turnos: ['Manana', 'Tarde', 'Noche'] },
        { nombre: 'Martes', turnos: ['Manana', 'Tarde', 'Noche'] },
        { nombre: 'Miércoles', turnos: ['Manana', 'Tarde', 'Noche'] },
        { nombre: 'Jueves', turnos: ['Manana', 'Tarde', 'Noche'] },
        { nombre: 'Viernes', turnos: ['Manana', 'Tarde', 'Noche'] },
        { nombre: 'Sábado', turnos: ['Manana', 'Tarde', 'Noche'] },
        { nombre: 'Domingo', turnos: ['Manana', 'Tarde', 'Noche'] }
    ];

    /**
     * Función genérica para obtener el ID de un elemento (día, turno, resumen)
     * basándose en si se proporciona un anuncioId o es el modal de Publicación.
     * @param {string} baseName - Nombre base del elemento (Ej: 'dia', 'LunesManana', 'resumenDisponibilidad').
     * @param {string} anuncioId - El ID del anuncio o null/undefined para Publicación.
     * @returns {string} El ID completo del elemento.
     */
    function buildElementId(baseName, anuncioId) {
        if (baseName.startsWith('resumenDisponibilidad') && !anuncioId) {
             // Caso especial para el ID del resumen en el modal de Publicación
            return '#resumenDisponibilidadPublicar'; 
        }
        // Caso Edición o cualquier otro elemento en Publicación
        return `#${baseName}${anuncioId || ''}`;
    }

    /**
     * -------------------------------------------------------------------------------------
     * FUNCIÓN CORE: Configura los listeners y la lógica de resumen para CUALQUIER modal.
     * -------------------------------------------------------------------------------------
     */
    function configurarModalDisponibilidad(modalElement, anuncioId) {
        console.log(`[DEBUG - CORE] 🔧 Configuracion CORE iniciada para ID: ${anuncioId || 'PUBLICACION'}`);

        // --- FUNCIÓN DE RESUMEN (Unificada) ---
        function actualizarResumen() {
            console.log('[DEBUG - RESUMEN] --- Ejecutando actualizarResumen ---');

            // 1. Obtener el elemento del resumen. Usa el selector específico si es Publicación.
            const resumenSelector = buildElementId('resumenDisponibilidad', anuncioId);
            const resumenDisponibilidad = modalElement.querySelector(resumenSelector);

            if (!resumenDisponibilidad) {
                console.error(`[DEBUG - INIT] 🛑 Elemento ${resumenSelector} no encontrado. Abortando resumen.`);
                return;
            }

            const diasSeleccionados = [];
            const turnosTotales = { Manana: 0, Tarde: 0, Noche: 0 };

            diasData.forEach(dia => {
                let turnosDia = 0;
                
                // Usamos un selector general para encontrar los checkboxes de turno dentro del modal
                // Los IDs de los turnos en el HTML de publicación no tienen ID de anuncio, pero los names sí.
                // Usaremos la propiedad name, que siempre es 'turnos_Dia[]'
                
                dia.turnos.forEach((turnoAbrv, index) => {
                    const turnoValue = ['M', 'T', 'N'][index];
                    const turnoCheckbox = modalElement.querySelector(`input[name="turnos_${dia.nombre}[]"][value="${turnoValue}"]`);

                    if (turnoCheckbox) {
                        if (turnoCheckbox.checked) {
                            turnosDia++;
                            turnosTotales[dia.turnos[index]] = (turnosTotales[dia.turnos[index]] || 0) + 1;
                            console.log(`[DEBUG - RESUMEN] ✅ Turno ${dia.nombre}-${dia.turnos[index]} está MARCADO.`);
                        } else {
                            console.log(`[DEBUG - RESUMEN] ⚪ Turno ${dia.nombre}-${dia.turnos[index]} está DESMARCADO.`);
                        }
                    } else {
                       // console.warn(`[DEBUG - RESUMEN] ⚠️ Checkbox para ${dia.nombre}-${dia.turnos[index]} NO encontrado.`);
                    }
                });

                if (turnosDia > 0) diasSeleccionados.push(dia.nombre);
            });

            console.log(`[DEBUG - RESUMEN] Días con turnos seleccionados: ${diasSeleccionados.join(', ')}`);
            
            let resumen = 'No hay disponibilidad seleccionada';
            if (diasSeleccionados.length > 0) {
                const turnosSeleccionados = [];
                if (turnosTotales.Manana > 0) turnosSeleccionados.push('Mañana');
                if (turnosTotales.Tarde > 0) turnosSeleccionados.push('Tarde');
                if (turnosTotales.Noche > 0) turnosSeleccionados.push('Noche');

                const diasNombres = diasData.map(d => d.nombre);
                const primerDiaSeleccionado = diasSeleccionados[0];
                const ultimoDiaSeleccionado = diasSeleccionados[diasSeleccionados.length - 1];

                const indexPrimer = diasNombres.indexOf(primerDiaSeleccionado);
                const indexUltimo = diasNombres.indexOf(ultimoDiaSeleccionado);
                
                // Verifica si todos los días seleccionados son consecutivos
                const sonConsecutivos = (indexUltimo - indexPrimer + 1) === diasSeleccionados.length && diasSeleccionados.length > 1;

                if (diasSeleccionados.length === 7) {
                    resumen = `Disponible todos los días en turnos de ${turnosSeleccionados.join(', ').replace(/, ([^,]*)$/, ' y $1')}`;
                } else if (sonConsecutivos) {
                    resumen = `Disponible de ${primerDiaSeleccionado} a ${ultimoDiaSeleccionado} en turnos de ${turnosSeleccionados.join(', ').replace(/, ([^,]*)$/, ' y $1')}`;
                } else {
                    resumen = `Disponible los ${diasSeleccionados.join(', ').replace(/, ([^,]*)$/, ' y $1')} en turnos de ${turnosSeleccionados.join(', ').replace(/, ([^,]*)$/, ' y $1')}`;
                }
            }
            console.log(`[DEBUG - RESUMEN] Resumen final: ${resumen}`);
            resumenDisponibilidad.textContent = resumen;
        }


        // --- FUNCIÓN DE VALIDACIÓN (Añadida para consistencia, aunque no usada en Publicación) ---
        function validarFormulario(event) {
            console.log('[DEBUG - VALIDATION] 📩 Evento submit disparado.');
            let totalTurnosSeleccionados = 0;

            diasData.forEach(dia => {
                dia.turnos.forEach((turnoAbrv, index) => {
                    const turnoValue = ['M', 'T', 'N'][index];
                    const turnoCheckbox = modalElement.querySelector(`input[name="turnos_${dia.nombre}[]"][value="${turnoValue}"]`);
                    
                    if (turnoCheckbox && turnoCheckbox.checked) {
                        totalTurnosSeleccionados++;
                    }
                });
            });

            console.log(`[DEBUG - VALIDATION] Total de turnos seleccionados: ${totalTurnosSeleccionados}.`);
            
            diasData.forEach(dia => {
                const dayCheckbox = modalElement.querySelector(`input[name="dias[]"][value="${dia.nombre}"]`);
                if (dayCheckbox) {
                    console.log(`[DEBUG - VALIDATION] Estado final (OCULTO) ${dia.nombre}: ${dayCheckbox.checked}`);
                }
            });
            
            console.log(`[DEBUG - VALIDATION] ✅ Envío de formulario permitido.`);

            return true;
        }


        // --- FUNCIÓN DE AUTO-MARCADO DE DÍA (Unificada) ---
        function actualizarCheckboxDia(dia, isChecked) {
            // Busca el checkbox oculto por su nombre y valor
            const dayCheckbox = modalElement.querySelector(`input[name="dias[]"][value="${dia}"]`);
            if (!dayCheckbox) return;

            if (isChecked) {
                if (!dayCheckbox.checked) {
                    console.log(`[DEBUG - AUTO-CHECK] 🟢 Marcando día ${dia} automáticamente.`);
                    dayCheckbox.checked = true;
                }
            } else {
                // Comprobamos si queda algún otro turno marcado para este día
                const anyTurnoChecked = diasData.find(d => d.nombre === dia).turnos.some((turnoAbrv, index) => {
                    const turnoValue = ['M', 'T', 'N'][index];
                    const tCheck = modalElement.querySelector(`input[name="turnos_${dia}[]"][value="${turnoValue}"]`);
                    return tCheck && tCheck.checked;
                });

                if (!anyTurnoChecked) {
                    console.log(`[DEBUG - AUTO-UNCHECK] 🔴 Desmarcando día ${dia} automáticamente.`);
                    dayCheckbox.checked = false; // Desmarca el input oculto si no quedan turnos
                } else {
                    console.log(`[DEBUG - AUTO-UNCHECK] 🟡 No se desmarca ${dia}, aún quedan turnos activos.`);
                }
            }
            console.log(`[DEBUG - AUTO-STATE] Nuevo estado (OCULTO) ${dia}: ${dayCheckbox.checked}`);
        }

        // --- Asignar Event Listeners ---

        const form = modalElement.querySelector('form');
        if (form) {
            console.log(`[DEBUG - FORM] Formulario encontrado. Action: ${form.action}`);
            // Usa el evento submit para la validación (se mantiene tu lógica)
            form.addEventListener('submit', validarFormulario);
        }

        // Asignar listeners a todos los checkboxes de turno
        diasData.forEach(dia => {
            dia.turnos.forEach((turnoAbrv, index) => {
                const turnoValue = ['M', 'T', 'N'][index];
                const turnoCheckbox = modalElement.querySelector(`input[name="turnos_${dia.nombre}[]"][value="${turnoValue}"]`);

                if (turnoCheckbox) {
                    turnoCheckbox.addEventListener('change', function () {
                        console.log(`[DEBUG - CHANGE] 🔄 Turno ${dia.nombre}-${turnoAbrv} cambiado a: ${this.checked}`);
                        
                        actualizarCheckboxDia(dia.nombre, this.checked);
                        actualizarResumen();
                    });
                }
            });
        });
        
        // Inicializar el resumen al abrir el modal
        modalElement.addEventListener('shown.bs.modal', function () {
            actualizarResumen();
        });
        
        // Ejecutar el resumen al inicio (para el estado inicial cargado de Edición o el estado desmarcado de Publicación)
        actualizarResumen();
    }


    /**
     * -------------------------------------------------------------
     * FUNCIÓN ORIGINAL DE EDICIÓN (ADAPTADA)
     * -------------------------------------------------------------
     * Esta función actúa como puente para el código de edición existente,
     * llamando a la nueva función `configurarModalDisponibilidad`.
     */
    function inicializarDisponibilidad(modalElement, anuncioId) {
        console.log(`[DEBUG - ORIGINAL-INIT] 🔑 Llamando a CORE para Edición ID: ${anuncioId}`);
        // La lógica se ha movido a configurarModalDisponibilidad, solo la llamamos
        configurarModalDisponibilidad(modalElement, anuncioId);
    }
    
    // Inicialización de la lógica al abrir el modal (SIN CAMBIOS - SE MANTIENE EL CÓDIGO FUNCIONAL DE EDICIÓN)
    const editModals = document.querySelectorAll('[id^="editarTutoriaModal"]');

    editModals.forEach(modalElement => {
        if (typeof bootstrap !== 'undefined') {
            const modalId = modalElement.id;
            const anuncioId = modalId.replace('editarTutoriaModal', '');

            // Se usa el evento 'shown' para asegurar que los datos iniciales de Edición estén listos
            modalElement.addEventListener('shown.bs.modal', function () {
                inicializarDisponibilidad(modalElement, anuncioId);
            });
            // También se llama directamente para que funcione si el modal se carga visible, aunque no es común.
            // inicializarDisponibilidad(modalElement, anuncioId); 
        }
    });

    // -------------------------------------------------------------
    // NUEVA LÓGICA DE INICIALIZACIÓN PARA PUBLICACIÓN
    // -------------------------------------------------------------
    const publicarModalElement = document.getElementById('publicarTutoriaModal');
    if (publicarModalElement) {
        console.log(`[DEBUG - INIT] 🆕 Inicializando modal de Publicación.`);
        // Llamamos a la función CORE sin un anuncioId
        configurarModalDisponibilidad(publicarModalElement, null);
    }
    
    // Código original de efectos hover de tarjetas (SIN CAMBIOS)
    const hoverCardsMistutorias = document.querySelectorAll('.hover-card');
    hoverCardsMistutorias.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transition = 'all 0.3s ease';
        });
    });
});