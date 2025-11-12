document.addEventListener("DOMContentLoaded", function () {

    console.log("Documento cargado y listo");

    // 4. EFECTO SMOOTH SCROLL PARA NAVEGACIÓN
    document.querySelectorAll('.nav-link[href^="#"]').forEach(link => {
        link.addEventListener('click', function (e) {
            if (this.hash !== "") {
                e.preventDefault();
                const hash = this.hash;
                const target = document.querySelector(hash);
                if (target) {
                    window.scrollTo({
                        top: target.offsetTop - 70,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // 5. ANIMACIÓN DE NAVBAR SECUNDARIO AL SCROLL
    let lastScrollTop = 0;
    window.addEventListener('scroll', function () {
        const st = window.scrollY || document.documentElement.scrollTop;
        const navbar = document.getElementById('secondary-navbar');
        const navbarMobile = document.getElementById('secondary-navbar-mobile');

        if (navbar) {
            if (st > lastScrollTop && st > 100) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }
        }

        if (navbarMobile) {
            if (st > lastScrollTop && st > 100) {
                navbarMobile.style.transform = 'translateY(-100%)';
            } else {
                navbarMobile.style.transform = 'translateY(0)';
            }
        }

        lastScrollTop = st;
    });

    // 6. INDICADOR DE PÁGINA ACTIVA MEJORADO
    function resaltarEnlaceActivo() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.navbar-secondary .nav-link, .navbar-secondary-mobile .nav-link').forEach(link => {
            const linkPath = link.getAttribute('href');
            if (linkPath === currentPath ||
                (currentPath.startsWith(linkPath) && linkPath !== '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // 7. FUNCIÓN DE NOTIFICACIONES
    function mostrarNotificacion(mensaje, tipo = 'info') {
        const tipos = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        };

        const wrapper = document.createElement('div');
        wrapper.className = `alert ${tipos[tipo]} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        wrapper.style.zIndex = "9999";
        wrapper.style.minWidth = "300px";
        wrapper.innerHTML = `
        <i class="bi bi-${tipo === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      `;

        document.body.appendChild(wrapper);

        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(wrapper);
            alert.close();
        }, 4000);
    }

    // 9. EFECTO HOVER MEJORADO PARA NAV LINKS
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('mouseenter', () => {
            link.style.transform = 'translateY(-1px)';
        });
        link.addEventListener('mouseleave', () => {
            link.style.transform = 'translateY(0)';
        });
    });

    // INICIALIZACIÓN
    resaltarEnlaceActivo();

});



