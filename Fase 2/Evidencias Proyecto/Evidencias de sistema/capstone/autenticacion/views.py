import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, LoginForm, validar_foto
from .models import Rol, Usuario, AreaInteres, Ocupacion
from PIL import Image
from django.core.signing import Signer, BadSignature, TimestampSigner, SignatureExpired
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

signer = Signer()

def enviar_verificacion_email(usuario, request):
    # genera un token firmado con el id del usuario
    token = signer.sign(usuario.id)
    # link completo
    activation_link = request.build_absolute_uri(f"/activar/{token}/")
    
    # enviar correo
    send_mail(
        subject="Activa tu cuenta",
        message=f"Hola {usuario.nombre}.\n\nactiva tu cuenta aquí: {activation_link}",
        from_email="lucaspoblete638@gmail.com",
        recipient_list=[usuario.email],
        fail_silently=False,
    )

def verificar_email(request, token):
    try:
        # decodifica el token
        user_id = signer.unsign(token)
        usuario = get_object_or_404(Usuario, id=user_id)
        if usuario.is_active:
            messages.info(request, "Tu cuenta ya está activada. Puedes iniciar sesión.")
        else:
            usuario.is_active = True
            usuario.estado = "Activo"
            usuario.save()
            messages.success(request, "Cuenta activada correctamente. Ya puedes iniciar sesión.")
            return redirect("login")
    except SignatureExpired:
        messages.error(request, "El link de activación ha expirado.")
    except BadSignature:
        messages.error(request, "El link de activación no es válido.")
    return redirect("login")


def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Crear usuario sin guardar aún
                user = form.save(commit=False)
                user.is_active = False

                # Validar y guardar foto si hay
                foto = form.cleaned_data.get('foto')
                if foto:
                    try:
                        validar_foto(foto)
                        user.foto = foto.read()
                    except ValueError as e:
                        messages.error(request, str(e))

                user.save()

                # Asignar rol estudiante
                rol_estudiante = Rol.objects.get(nombre="Estudiante")
                user.roles.add(rol_estudiante)

                # Enviar correo de verificación
                enviar_verificacion_email(user, request)

                # Guardar campos ManyToMany del form (áreas de interés)
                form.save_m2m()

                messages.success(request, "Registro exitoso. Revisa tu correo para activar tu cuenta.")
                return redirect('login')

            except Exception:
                messages.error(request, "Hubo un error en el registro")
                logger.error("Error creando usuario", exc_info=True)

        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = RegistroForm()

    areas = AreaInteres.objects.all()
    ocupaciones = Ocupacion.objects.all()

    contexto = {
        'form': form,
        'areas': areas,
        'ocupaciones': ocupaciones
    }

    return render(request, 'autenticacion/registro.html', contexto)

@login_required
def seleccionar_rol(request):
    try:
        if request.method == "POST":
            rol_seleccionado = request.POST.get("rol")
            request.session['rol_actual'] = rol_seleccionado

            messages.success(request, f'¡Bienvenido de nuevo, {request.user.nombre}!')
            logger.info(f"Usuario {request.user.id} seleccionó el rol {rol_seleccionado}")
            return redirect('home')

        roles = request.session.get('roles_disponibles', [])
        contexto = {"roles": roles}
        return render(request, "autenticacion/seleccionar_rol.html", contexto)

    except Exception as e:
        messages.error(request, "Ocurrió un error al seleccionar el rol")
        logger.error(f"Error en seleccionar_rol para usuario {request.user.id}: {e}", exc_info=True)
        return redirect('home')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            try:
                user = authenticate(request, email=email, password=password)
                
                if user is not None:
                    login(request, user)
                    
                    # Consultar los roles del usuario
                    roles = list(user.roles.values_list('nombre', flat=True))
                    print(roles)

                    if "Tutor" in roles and "Estudiante" in roles:
                        # Usuario tiene ambos roles -> mostrar modal
                        request.session['roles_disponibles'] = roles
                        return redirect('seleccionar_rol')
                    else:
                        # Usuario tiene solo un rol -> guardar en sesión
                        request.session['rol_actual'] = roles[0]
                        return redirect('home')
            except Exception:
                messages.error(request, 'Hubo un error al inicar sesión. Inténtalo nuevamente.')
                logger.error(f'Hubo un error al iniciar sesión', exc_info=True)
                return redirect("login")
            else:
                messages.error(request, 'Correo o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = LoginForm()
    
    return render(request, 'autenticacion/login.html', {'form': form})

