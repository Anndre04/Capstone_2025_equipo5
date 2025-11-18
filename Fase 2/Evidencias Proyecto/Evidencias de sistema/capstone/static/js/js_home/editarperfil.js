document.addEventListener("DOMContentLoaded", function () {

    // --- REGION -> COMUNA ---
    const regionSelect = document.getElementById("region-select");
    const comunaSelect = document.getElementById("comuna-select");
    const allComunas = Array.from(comunaSelect.options);

    const fileInput = document.getElementById('id_certificacion');
    const listaArchivos = document.getElementById('lista-archivos-seleccionados');

    function filterComunas() {
        const selectedRegion = regionSelect.value;
        comunaSelect.innerHTML = '<option value="">--Seleccione--</option>'; // Reset

        allComunas.forEach(option => {
            if (!selectedRegion || option.dataset.region === selectedRegion) {
                comunaSelect.appendChild(option);
            }
        });

        if (comunaSelect.selectedOptions.length > 0 &&
            comunaSelect.selectedOptions[0].dataset.region !== selectedRegion) {
            comunaSelect.value = "";
        }
    }

    regionSelect.addEventListener("change", filterComunas);
    filterComunas();

    // --- TOMSELECT ---
    new TomSelect("#areas_interes", {
        plugins: ["remove_button"],
        create: false,
        maxItems: null,
        placeholder: "Selecciona tus áreas de interés",
        dropdownClass: "ts-dropdown dropdown-menu show",
    });

    new TomSelect("#areas_conocimiento", {
        plugins: ["remove_button"],
        create: false,
        maxItems: null,
        placeholder: "Selecciona áreas de conocimiento",
        dropdownClass: "ts-dropdown dropdown-menu show"
    });

    // --- VALIDACIÓN OCUPACIÓN ---
    const ocupacionSelect = document.querySelector("select[name='ocupacion']");
    const nivelEducSelect = document.querySelector("select[name='n_educacion']");
    const institucionSelect = document.querySelector("select[name='institucion']");

    function validarOcupacion() {
        const val = ocupacionSelect.selectedOptions[0]?.text.toLowerCase();

        if (val === "trabajador" || val === "ninguna") {
            // Deshabilitar selects
            nivelEducSelect.disabled = true;
            institucionSelect.disabled = true;

            // Seleccionar "No aplica"
            const nivelNoAplica = Array.from(nivelEducSelect.options).find(opt => opt.text.toLowerCase() === "no aplica");
            if (nivelNoAplica) nivelEducSelect.value = nivelNoAplica.value;

            const institucionNoAplica = Array.from(institucionSelect.options).find(opt => opt.text.toLowerCase() === "no aplica");
            if (institucionNoAplica) institucionSelect.value = institucionNoAplica.value;

        } else {
            // Habilitar selects y limpiar selección si estaba "No aplica"
            nivelEducSelect.disabled = false;
            institucionSelect.disabled = false;

            if (nivelEducSelect.selectedOptions[0]?.text.toLowerCase() === "no aplica") {
                nivelEducSelect.value = "";
            }
            if (institucionSelect.selectedOptions[0]?.text.toLowerCase() === "no aplica") {
                institucionSelect.value = "";
            }
        }
    }

    ocupacionSelect.addEventListener("change", validarOcupacion);
    validarOcupacion();

    if (!fileInput || !listaArchivos) return;

    let selectedFiles = [];
    let fileNames = [];

    function renderFileList() {
        listaArchivos.innerHTML = '';

        if (selectedFiles.length === 0) {
            const li = document.createElement('li');
            li.className = 'list-group-item text-muted';
            li.textContent = 'Ningún archivo seleccionado.';
            listaArchivos.appendChild(li);
            return;
        }

        selectedFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex align-items-center justify-content-between p-2';

            const leftDiv = document.createElement('div');
            leftDiv.className = 'd-flex align-items-center flex-grow-1';

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-sm btn-outline-danger me-2 p-1';
            removeBtn.innerHTML = '<i class="bi bi-x"></i>';
            removeBtn.setAttribute('data-index', index);
            removeBtn.title = 'Eliminar este archivo';

            const nameSpan = document.createElement('span');
            nameSpan.className = 'fw-medium text-truncate small me-3';
            nameSpan.textContent = file.name;

            leftDiv.appendChild(removeBtn);
            leftDiv.appendChild(nameSpan);

            const inputName = document.createElement('input');
            inputName.type = 'text';
            inputName.name = `nombre_archivo_${index}`;
            inputName.placeholder = 'Cambia nombre del archivo';
            inputName.className = 'form-control form-control-sm w-50';
            inputName.maxLength = 80;
            inputName.value = fileNames[index] || file.name.replace(/\.[^/.]+$/, "");
            inputName.addEventListener('input', e => fileNames[index] = e.target.value);

            li.appendChild(leftDiv);
            li.appendChild(inputName);
            listaArchivos.appendChild(li);
        });

        updateFileInput();
    }

    function updateFileInput() {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => dataTransfer.items.add(file));
        fileInput.files = dataTransfer.files;
    }

    fileInput.addEventListener('change', function () {
        selectedFiles = Array.from(fileInput.files);
        fileNames = new Array(selectedFiles.length).fill(null);
        renderFileList();
    });

    listaArchivos.addEventListener('click', function (event) {
        const btn = event.target.closest('[data-index]');
        if (!btn) return;
        const index = parseInt(btn.dataset.index);
        selectedFiles.splice(index, 1);
        fileNames.splice(index, 1);
        renderFileList();
    });

    renderFileList();
});
