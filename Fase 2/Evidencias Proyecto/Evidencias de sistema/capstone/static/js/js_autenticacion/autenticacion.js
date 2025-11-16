// ===== REGISTRO =====

document.addEventListener('DOMContentLoaded', function () {

  // 🌟 Eliminamos las referencias a áreasGrid, selectedTagsContainer, areasInteresInput
  // const areasGrid = document.getElementById('areasGrid');
  // const selectedTagsContainer = document.getElementById('selectedTags');
  // const areasInteresInput = document.getElementById('areasInteresInput');
  const toggleButtons = document.querySelectorAll('.toggle-password');

  const paisSelect = document.getElementById("id_pais");
  const regionSelect = document.getElementById("id_region");
  const comunaSelect = document.getElementById("id_comuna");

  const ocupacionSelect = document.getElementById('ocupacion');
  const nivelDiv = document.getElementById('div_nivel_educacional');
  const institucionDiv = document.getElementById('div_institucion');
  const nivelSelect = document.getElementById('id_nivel_educacional');

  // Deshabilita al inicio
  regionSelect.disabled = true;
  comunaSelect.disabled = true;

  function actualizarTodo() {
    // ===== País / Región / Comuna =====
    const paisSeleccionado = paisSelect.options[paisSelect.selectedIndex].text.trim();
    if (paisSeleccionado === "Chile") {
      regionSelect.disabled = false;
    } else {
      regionSelect.disabled = true;
      comunaSelect.disabled = true;
      regionSelect.value = "";
      comunaSelect.value = "";
    }

    // ===== Ocupación (siempre visible) =====
    const ocupacion = ocupacionSelect.value;

    // ===== Nivel / Institución (solo si país es Chile) =====
    if (paisSeleccionado === "Chile") {

      const ocupacionText = ocupacionSelect.options[ocupacionSelect.selectedIndex].text.trim();

      if (ocupacionText === 'Estudiante' || ocupacionText === 'Ambos') {
        nivelDiv.style.display = 'block';
      } else {
        nivelDiv.style.display = 'none';
        institucionDiv.style.display = 'none';
      }

      const nivelText = nivelSelect ? nivelSelect.options[nivelSelect.selectedIndex].text.trim() : '';

      if (nivelText === 'Educación Superior' && (ocupacionText === 'Estudiante' || ocupacionText === 'Ambos')) {
        institucionDiv.style.display = 'block';
      } else {
        institucionDiv.style.display = 'none';
      }
    } else {
      nivelDiv.style.display = 'none';
      institucionDiv.style.display = 'none';
    }
  }

  function togglePasswordVisibility() {
    // Seleccionamos todos los botones que tienen la clase 'toggle-password'
    const toggleButtons = document.querySelectorAll('.toggle-password');

    toggleButtons.forEach(button => {
      button.addEventListener('click', function () {
        // 1. Obtener el ID del input objetivo desde el atributo data-target (e.g., "#id_password1")
        const targetId = this.dataset.target;
        const passwordInput = document.querySelector(targetId);

        if (!passwordInput) return; // Si el input no existe, salimos

        // 2. Cambiar el atributo 'type' entre 'password' y 'text'
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // 3. Actualizar el icono del botón (asumiendo Bootstrap Icons: bi-eye / bi-eye-slash)
        const icon = this.querySelector('i');
        if (icon) {
          if (type === 'text') {
            // Mostrar ojo tachado si está visible
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
          } else {
            // Mostrar ojo normal si está oculto
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
          }
        }
      });
    });
  }


  // Event listeners
  paisSelect.addEventListener("change", actualizarTodo);
  regionSelect.addEventListener("change", function () {
    const regionId = this.value;

    if (regionId) {
      comunaSelect.disabled = false;
      comunaSelect.innerHTML = '<option value="">Cargando...</option>';

      fetch(`/auth/obtener_comunas/${regionId}/`)
        .then(response => response.json())
        .then(data => {
          comunaSelect.innerHTML = '<option value="">Seleccione comuna</option>';
          data.forEach(comuna => {
            const option = document.createElement('option');
            option.value = comuna.id;
            option.textContent = comuna.nombre;
            comunaSelect.appendChild(option);
          });
        })
        .catch(error => console.error("Error cargando comunas:", error));
    } else {
      comunaSelect.disabled = true;
      comunaSelect.innerHTML = '<option value="">Seleccione comuna</option>';
    }

    actualizarTodo();
  });

  ocupacionSelect.addEventListener('change', actualizarTodo);
  if (nivelSelect) {
    nivelSelect.addEventListener('change', actualizarTodo);
  }

  // Ejecutar al cargar la página
  actualizarTodo();
  togglePasswordVisibility();

  document.querySelectorAll('.tomselect-multiple').forEach((select) => {
    const ts = new TomSelect(select, {
        plugins: ['remove_button'],
        maxItems: null,
        hideSelected: true,
        placeholder: select.selectedOptions.length === 0 ? 'Selecciona una o más opciones...' : '',
    });

    // Forzar que el wrapper tenga clases de Bootstrap
    if (ts.wrapper) {
        ts.wrapper.classList.add('form-control', 'form-control-sm');
        ts.wrapper.style.minHeight = 'calc(1.5em + 0.75rem + 2px)'; // altura de form-control-sm
    }
});


  const hoy = new Date();
  const minEdad = 13;
  const maxEdad = 115;
  const fechaMaxima = new Date(hoy.getFullYear() - minEdad, hoy.getMonth(), hoy.getDate());
  const fechaMinima = new Date(hoy.getFullYear() - maxEdad, hoy.getMonth(), hoy.getDate());

  const pickerNacimiento = new tempusDominus.TempusDominus(
    document.getElementById("datetimepicker-fechanac"),
    {
      display: {
        components: {
          calendar: true,
          date: true,
          month: true,
          year: true,
          decades: true,
          clock: false // ❌ sin hora
        },
      },
      localization: {
        locale: 'es',
        format: 'yyyy-MM-dd', // ✅ formato solo fecha
        dayViewHeaderFormat: { month: 'long', year: 'numeric' }
      },
      restrictions: {
        minDate: fechaMinima,
        maxDate: fechaMaxima
      },
      useCurrent: false // evita hora por defecto
    }
  );

  // Mostrar calendario al enfocar o hacer click
  const inputNacimiento = document.getElementById('fecha_nac');
  inputNacimiento.addEventListener('focus', () => pickerNacimiento.show());
  inputNacimiento.addEventListener('click', () => pickerNacimiento.show());

  // Actualizar input con fecha seleccionada
  inputNacimiento.addEventListener("change.td", (e) => {
    if (e.detail?.date) {
      const date = e.detail.date;
      const year = date.year;
      const month = String(date.month + 1).padStart(2, "0");
      const day = String(date.date).padStart(2, "0");
      inputNacimiento.value = `${year}-${month}-${day}`; // solo YYYY-MM-DD
    }
  });

});