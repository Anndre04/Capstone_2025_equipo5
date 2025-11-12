
document.addEventListener('DOMContentLoaded', function () {

    const banner = document.getElementById('registro-banner');
    const tutorBanner = document.getElementById('tutor-promo-banner');
    const slider = document.getElementById('precio-slider');
    const label = document.getElementById('precio-label');
    const hiddenInput = document.getElementById('precio_max');

    if (banner) {
        // 1. Forzamos un pequeño retraso (incluso 0ms) para asegurar que el navegador 
        // ha aplicado el CSS inicial (opacity: 0) antes de aplicar el CSS final (opacity: 1).
        // Esto es un truco común para asegurar que la transición CSS se dispara correctamente.
        setTimeout(() => {
            banner.style.opacity = '1'; // 👈 Esto activa la transición de 1 segundo
            
            // OPCIONAL: Si quieres neutralizar cualquier otra animación, puedes dejar esto:
            banner.style.setProperty('transition', 'opacity 1s ease-in-out', 'important');
            
            console.log("✅ Promo Banner activando fade-in.");
        }, 50); // 50ms es más que suficiente para disparar la transición.
    }

    if (tutorBanner) {
        // 1. Forzamos un pequeño retraso para asegurar que el navegador 
        // ha aplicado el CSS inicial (opacity: 0) antes de aplicar el CSS final (opacity: 1).
        setTimeout(() => {
            tutorBanner.style.opacity = '1'; // 👈 Esto activa la transición de 1 segundo
            
            // Opcional: Para anular cualquier transición conflictiva de terceros
            tutorBanner.style.setProperty('transition', 'opacity 1s ease-in-out', 'important');
            
            console.log("✅ Promo Banner de Tutor activando fade-in.");
        }, 50); 
    }

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