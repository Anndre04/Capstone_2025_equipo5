from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, LoginForm
from .models import Rol

def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = True
                user.estado = 'Activo'
                user.save()
                
                form.save_m2m()
                
                rol_estudiante = Rol.objects.get_or_create(nombre='Estudiante')
                user.roles.add(rol_estudiante)
                
                login(request, user)
                messages.success(request, '¡Registro exitoso! Bienvenido/a.')
                return redirect('dashboard')
                
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
        return redirect('home')  # O dashboard según tu lógica

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

