
// Vistas incluidas:
// - anunciotutor.html
// - gestortutorias.html
// - mistutoriasprof.html
// - solicitudesprof.html


document.addEventListener('DOMContentLoaded', function () {
  console.log('✅ Archivo tutoria.js cargado correctamente');


  // SECCIÓN: ANUNCIOTUTOR.HTML

  /* const downloadButtons = document.querySelectorAll('.btn-outline-primary');
  if (downloadButtons.length > 0) {
    console.log(' Vista de Tutoría - Anuncio cargada correctamente');
    downloadButtons.forEach(button => {
      button.addEventListener('click', function () {
        const fileName = this.closest('.border')?.querySelector('h6')?.textContent || 'Archivo';
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';
        alert.innerHTML = `
          <div class="d-flex align-items-center">
              <i class="bi bi-check-circle-fill me-2"></i>
              <span class="flex-grow-1">Iniciando descarga: ${fileName}</span>
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 3000);
      });
    });
  } */

  const tutorCards = document.querySelectorAll('.card');
  tutorCards.forEach(card => {
    card.addEventListener('mouseenter', function () {
      this.style.transition = 'all 0.3s ease';
    });
  });


  // SECCIÓN: GESTORTUTORIAS.HTML


  const picker = new tempusDominus.TempusDominus(
    document.getElementById("datetimepicker-fechagestortutoria"),
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
  inputFecha.addEventListener('focus', () => picker.show());
  inputFecha.addEventListener('click', () => picker.show());

  // 🔧 Al seleccionar una fecha, la formateamos sin hora
  const input = document.getElementById("fechagestortutoria");
  document
    .getElementById("datetimepicker-fechagestortutoria")
    .addEventListener("change.td", (e) => {
      if (e.detail?.date) {
        const date = e.detail.date;
        const year = date.year;
        const month = String(date.month + 1).padStart(2, "0");
        const day = String(date.date).padStart(2, "0");
        input.value = `${year}-${month}-${day}`;
      }
    });


  //  SECCIÓN: MISTUTORIASPROF.HTML

  const resumenDisponibilidad = document.getElementById('resumenDisponibilidad');
  if (resumenDisponibilidad) {
    console.log(' Mis Tutorías Profesor - Vista cargada');

    const dias = [
      { nombre: 'Lunes', idDia: 'diaLunes', turnos: ['LunesManana', 'LunesTarde', 'LunesNoche'] },
      { nombre: 'Martes', idDia: 'diaMartes', turnos: ['MartesManana', 'MartesTarde', 'MartesNoche'] },
      { nombre: 'Miércoles', idDia: 'diaMiercoles', turnos: ['MiercolesManana', 'MiercolesTarde', 'MiercolesNoche'] },
      { nombre: 'Jueves', idDia: 'diaJueves', turnos: ['JuevesManana', 'JuevesTarde', 'JuevesNoche'] },
      { nombre: 'Viernes', idDia: 'diaViernes', turnos: ['ViernesManana', 'ViernesTarde', 'ViernesNoche'] },
      { nombre: 'Sábado', idDia: 'diaSabado', turnos: ['SabadoManana', 'SabadoTarde', 'SabadoNoche'] },
      { nombre: 'Domingo', idDia: 'diaDomingo', turnos: ['DomingoManana', 'DomingoTarde', 'DomingoNoche'] }
    ];

    function actualizarResumen() {
      const diasSeleccionados = [];
      const turnosTotales = { manana: 0, tarde: 0, noche: 0 };

      dias.forEach(dia => {
        const diaCheckbox = document.getElementById(dia.idDia);
        if (diaCheckbox && diaCheckbox.checked) {
          let turnosDia = 0;
          dia.turnos.forEach((turnoId, index) => {
            const turnoCheckbox = document.getElementById(turnoId);
            if (turnoCheckbox && turnoCheckbox.checked) {
              turnosDia++;
              if (index === 0) turnosTotales.manana++;
              else if (index === 1) turnosTotales.tarde++;
              else if (index === 2) turnosTotales.noche++;
            }
          });
          if (turnosDia > 0) diasSeleccionados.push(dia.nombre);
        }
      });

      let resumen = 'No hay disponibilidad seleccionada';
      if (diasSeleccionados.length > 0) {
        const turnosSeleccionados = [];
        if (turnosTotales.manana > 0) turnosSeleccionados.push('Mañana');
        if (turnosTotales.tarde > 0) turnosSeleccionados.push('Tarde');
        if (turnosTotales.noche > 0) turnosSeleccionados.push('Noche');

        if (diasSeleccionados.length === 7)
          resumen = `Disponible todos los días en turnos de ${turnosSeleccionados.join(', ')}`;
        else if (diasSeleccionados.length >= 5)
          resumen = `Disponible de ${diasSeleccionados[0]} a ${diasSeleccionados[diasSeleccionados.length - 1]} en turnos de ${turnosSeleccionados.join(', ')}`;
        else
          resumen = `Disponible los ${diasSeleccionados.join(', ')} en turnos de ${turnosSeleccionados.join(', ')}`;
      }

      resumenDisponibilidad.textContent = resumen;
    }

    dias.forEach(dia => {
      const diaCheckbox = document.getElementById(dia.idDia);
      if (diaCheckbox) {
        diaCheckbox.addEventListener('change', function () {
          dia.turnos.forEach(turnoId => {
            const turnoCheckbox = document.getElementById(turnoId);
            if (turnoCheckbox) {
              turnoCheckbox.disabled = !this.checked;
              if (!this.checked) turnoCheckbox.checked = false;
            }
          });
          actualizarResumen();
        });
      }
      dia.turnos.forEach(turnoId => {
        const turnoCheckbox = document.getElementById(turnoId);
        if (turnoCheckbox) turnoCheckbox.addEventListener('change', actualizarResumen);
      });
    });

    actualizarResumen();

    // Efectos hover y tooltips
    const hoverCards = document.querySelectorAll('.hover-card');
    hoverCards.forEach(card => {
      card.addEventListener('mouseenter', function () {
        this.style.transition = 'all 0.3s ease';
      });
    });

    const editButtons = document.querySelectorAll('.btn-outline-primary');
    editButtons.forEach(button => {
      button.addEventListener('click', function () {
        const cardTitle = this.closest('.card')?.querySelector('.card-title')?.textContent || 'Tutoría';
        console.log(`Editando: ${cardTitle}`);
      });
    });

    if (typeof bootstrap !== 'undefined') {
      const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
      tooltipTriggerList.map(el => new bootstrap.Tooltip(el));
    }
  }


  // SECCIÓN: SOLICITUDESPROF.HTML

  const acceptButtons = document.querySelectorAll('.btn-success');
  const rejectButtons = document.querySelectorAll('.btn-outline-secondary');

  if (acceptButtons.length > 0 || rejectButtons.length > 0) {
    console.log('✅ Solicitudes Profesor - Vista cargada correctamente');

    function showNotification(message, type) {
      const alert = document.createElement('div');
      alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
      alert.style.zIndex = '9999';
      alert.style.minWidth = '300px';
      alert.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'info-circle'}-fill me-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      `;
      document.body.appendChild(alert);
      setTimeout(() => alert.remove(), 4000);
    }

    acceptButtons.forEach(button => {
      button.addEventListener('click', function () {
        const studentName = this.closest('.card')?.querySelector('.fw-bold')?.textContent || 'Estudiante';
        showNotification(`Solicitud de ${studentName} aceptada`, 'success');
        setTimeout(() => {
          const card = this.closest('.col-12');
          card.style.opacity = '0.6';
          this.disabled = true;
          this.nextElementSibling.disabled = true;
        }, 1000);
      });
    });

    /* rejectButtons.forEach(button => {
      button.addEventListener('click', function () {
        const studentName = this.closest('.card')?.querySelector('.fw-bold')?.textContent || 'Estudiante';
        showNotification(`Solicitud de ${studentName} rechazada`, 'secondary');
        setTimeout(() => {
          const card = this.closest('.col-12');
          card.style.opacity = '0.6';
          this.disabled = true;
          this.previousElementSibling.disabled = true;
        }, 1000);
      });
    }); */

    const cards = document.querySelectorAll('.hover-card');
    cards.forEach(card => {
      card.addEventListener('mouseenter', function () {
        this.style.transition = 'all 0.3s ease';
      });
    });

    const requestCards = document.querySelectorAll('.col-12 .card');
    requestCards.forEach((card, index) => {
      card.style.animationDelay = `${index * 0.1}s`;
    });
  }
});
