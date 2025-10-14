// ===== REGISTRO =====

document.addEventListener('DOMContentLoaded', function() {
  // ===== GESTIÓN DE ÁREAS DE INTERÉS =====
  const areasGrid = document.getElementById('areasGrid');
  const selectedTagsContainer = document.getElementById('selectedTags');
  const areasInteresInput = document.getElementById('areasInteresInput');

  // Inicializar etiquetas según áreas preseleccionadas
  if (areasInteresInput.value) {
    const preselectedIds = areasInteresInput.value.split(',').filter(id => id !== '');
    preselectedIds.forEach(id => {
      const option = areasGrid.querySelector(`.area-option[data-id="${id}"]`);
      if (option) {
        option.classList.add('selected');
        addTag(id, option.textContent);
      }
    });
  }

  // Manejar click en cada opción
  areasGrid.querySelectorAll('.area-option').forEach(option => {
    option.addEventListener('click', function() {
      const id = this.dataset.id;
      const text = this.textContent;

      this.classList.toggle('selected');

      if (this.classList.contains('selected')) {
        addTag(id, text);
      } else {
        removeTag(id);
      }

      updateAreasInteresInput();
    });
  });

  // Función para agregar una etiqueta
  function addTag(id, text) {
    if (selectedTagsContainer.querySelector(`.tag[data-id="${id}"]`)) return;

    const tag = document.createElement('div');
    tag.className = 'tag badge bg-primary me-2 mb-2 d-inline-flex align-items-center';
    tag.dataset.id = id;
    tag.innerHTML = `
      ${text}
      <span class="tag-remove ms-2" style="cursor: pointer; font-weight: bold;">&times;</span>
    `;

    tag.querySelector('.tag-remove').addEventListener('click', function(e) {
      e.stopPropagation();
      removeTag(id);

      const option = areasGrid.querySelector(`.area-option[data-id="${id}"]`);
      if (option) option.classList.remove('selected');

      updateAreasInteresInput();
    });

    selectedTagsContainer.appendChild(tag);
  }

  // Función para eliminar una etiqueta
  function removeTag(id) {
    const tag = selectedTagsContainer.querySelector(`.tag[data-id="${id}"]`);
    if (tag) tag.remove();
  }

  // Actualizar input oculto
  function updateAreasInteresInput() {
    const selectedIds = Array.from(selectedTagsContainer.querySelectorAll('.tag'))
                             .map(tag => tag.dataset.id);
    areasInteresInput.value = selectedIds.join(',');
    console.log('IDs seleccionados:', areasInteresInput.value);
  }
});