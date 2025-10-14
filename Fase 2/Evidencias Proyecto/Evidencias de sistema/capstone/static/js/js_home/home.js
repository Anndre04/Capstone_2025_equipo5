
document.addEventListener('DOMContentLoaded', function () {

    console.log('JS home cargado correctamente');


    const slider = document.getElementById('precio-slider');
    const label = document.getElementById('precio-label');
    const hiddenInput = document.getElementById('precio_max');

    slider.addEventListener('input', function () {
        const value = parseInt(slider.value);
        const formatted = new Intl.NumberFormat('es-CL', { minimumFractionDigits: 0 }).format(value);
        label.textContent = `$${formatted}`;
        hiddenInput.value = value;
    });


    // ANIMACION
    const cards = document.querySelectorAll('.tutoring-card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(15px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        card.style.transitionDelay = `${i * 0.1}s`;
        observer.observe(card);
    });

    // FILTROS
    const filtros = document.querySelectorAll('select[name], input[name]');
    filtros.forEach(filtro => {
        filtro.addEventListener('change', function () {
            console.log('🔍 Filtro aplicado:', this.name, this.value);
        });
    });
});