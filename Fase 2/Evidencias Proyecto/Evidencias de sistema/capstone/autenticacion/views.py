from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, LoginForm
from .models import Rol, Usuario
from PIL import Image
from django.core.signing import Signer, BadSignature, TimestampSigner, SignatureExpired
from django.core.mail import send_mail


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
                # Obtener la foto antes de guardar
                foto = form.cleaned_data.get('foto')

                if foto:
                    # Validar extensión
                    valid_extensions = ['jpg', 'jpeg', 'png']
                    extension = foto.name.split('.')[-1].lower()
                    if extension not in valid_extensions:
                        messages.error(request, "La imagen debe ser en formato JPG, JPEG o PNG.")
                        return render(request, 'autenticacion/registro.html', {'form': form})
                    # Validar tamaño máximo 8MB
                    if foto.size > 8 * 1024 * 1024:
                        messages.error(request, "La imagen no puede pesar más de 8 MB.")
                        return render(request, 'autenticacion/registro.html', {'form': form})

                    # Validar dimensiones mínimo 500x500
                    img = Image.open(foto)
                    if img.width > 500 or img.height > 500:
                        messages.error(request, "La imagen debe tener menos de 500px de ancho y alto.")
                        return render(request, 'autenticacion/registro.html', {'form': form})

                # Si pasa la validación, crear el usuario
                user = form.save(commit=False)
                user.is_active = False
                user.estado = 'Deshabilitado'

                if foto:
                    # Guardar la foto en binario
                    user.foto = foto.read()

                # Guardar usuario y relaciones
                user.save()
                form.save_m2m()

                # Asignar rol
                rol_estudiante, _ = Rol.objects.get_or_create(nombre='Estudiante')
                user.roles.add(rol_estudiante)

                enviar_verificacion_email(user, request)

                messages.success(request, "Registro exitoso. Revisa tu correo para activar tu cuenta.")
                return redirect('login')

            except Exception as e:
                messages.error(request, f'Error al crear el usuario: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()

    return render(request, 'autenticacion/registro.html', {'form': form})


def seleccionar_rol(request):
    if request.method == "POST":
        rol_seleccionado = request.POST.get("rol")
        request.session['rol_actual'] = rol_seleccionado
        return redirect('home')

    roles = request.session.get('roles_disponibles', [])
    return render(request, "autenticacion/seleccionar_rol.html", {"roles": roles})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Consultar los roles del usuario
                roles = list(user.roles.values_list('nombre', flat=True))

                if "Tutor" in roles and "Estudiante" in roles:
                    # Usuario tiene ambos roles -> mostrar modal
                    request.session['roles_disponibles'] = roles
                    messages.success(request, f'¡Bienvenido de nuevo, {user.nombre}!')
                    return redirect('seleccionar_rol')
                else:
                    # Usuario tiene solo un rol -> guardar en sesión
                    request.session['rol_actual'] = roles[0]
                    return redirect('home')

            else:
                messages.error(request, 'Correo o contraseña incorrectos.')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = LoginForm()
    
    return render(request, 'autenticacion/login.html', {'form': form})

