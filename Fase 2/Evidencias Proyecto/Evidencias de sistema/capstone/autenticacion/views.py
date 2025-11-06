import logging
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, LoginForm, validar_foto
from .models import Comuna, Rol, AreaInteres, Ocupacion, Usuario
from django.core.signing import Signer, SignatureExpired, BadSignature
from .tasks import enviar_verificacion_email_task
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from django.conf import settings

logger = logging.getLogger(__name__)

signer = Signer()

def verificar_email(request, token):
    try:
        # decodifica el token
        user_id = signer.unsign(token)
        usuario = get_object_or_404(Usuario, id=user_id)
        
        # Si el usuario ya está activo, informa y redirige
        if usuario.is_active:
            messages.info(request, "Tu cuenta ya está activada. Puedes iniciar sesión.")
            
        # Si el usuario NO está activo, procede a la activación
        else:
            usuario.is_active = True
            usuario.estado = "Activo"
            usuario.save() # Guarda los cambios en la base de datos
            
            messages.success(request, "Cuenta activada correctamente. Ya puedes iniciar sesión.")
            return redirect("login")
            
    except SignatureExpired:
        messages.error(request, "El link de activación ha expirado. Por favor, regístrate nuevamente o solicita un nuevo enlace.")
        
    except BadSignature:
        messages.error(request, "El link de activación no es válido o ha sido manipulado.")
        
    # En caso de error (expiración, firma inválida o si el usuario no existe),
    # siempre redirige a la página de inicio de sesión o a donde consideres adecuado.
    return redirect("login")

def fotogcp(archivo, email_usuario, carpeta='fotos_perfil'):
    """
    Sube un archivo a GCP, eliminando cualquier foto de perfil anterior para ese usuario.
    Retorna solo la ruta relativa del nuevo objeto.
    """

    # 1. Crear el objeto Client usando las credenciales
    GCP_CLIENT = storage.Client.from_service_account_json(
        settings.GOOGLE_APPLICATION_CREDENTIALS
    )
    
    # 2. Obtener el objeto Bucket (GCP_BUCKET) que tiene los métodos
    GCP_BUCKET = GCP_CLIENT.get_bucket(settings.GOOGLE_CLOUD_BUCKET)

    if GCP_BUCKET is None:
        raise Exception("Servicio de almacenamiento no disponible.")

    # 1. Definir la base del nombre del archivo (sin extensión)
    # Esto es lo que usaremos para buscar archivos existentes.
    nombre_base = f"{carpeta}/{email_usuario}"
    
    # 2. **BUSCAR Y ELIMINAR ARCHIVOS ANTIGUOS**
    
    # El método list_blobs permite filtrar por prefijo.
    # Buscamos todos los blobs que comienzan con la ruta y el email del usuario.
    blobs_a_eliminar = GCP_BUCKET.list_blobs(prefix=nombre_base)
    
    # Eliminamos cada blob encontrado
    for blob in blobs_a_eliminar:
        blob.delete()
    
    # 3. Definir el nombre del nuevo archivo (con extensión)
    extension = archivo.name.split('.')[-1]
    nombre_archivo_nuevo = f"{nombre_base}.{extension}"

    # 4. Subir el nuevo archivo
    blob_nuevo = GCP_BUCKET.blob(nombre_archivo_nuevo)
    
    # Si estás en el contexto de Django, recuerda que 'archivo' necesita 'seek(0)'
    # antes de la subida si ya fue leído (ej. en la validación).
    # archivo.seek(0)
    
    blob_nuevo.upload_from_file(archivo, content_type=archivo.content_type)

    # 5. Retornar solo la ruta relativa para guardar en la base de datos
    return nombre_archivo_nuevo

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
                        # 1. Validación local
                        validar_foto(foto)
                        
                        foto.seek(0)

                        # 2. Llamada a GCP
                        url_foto = fotogcp(foto, form.cleaned_data.get('email'))
                        
                        # 3. Asignación si la subida fue exitosa
                        user.foto = url_foto
                        
                    # 📢 Captura errores de validación (ValueError) y de Google Cloud
                    except ValueError as e:
                        messages.error(request, str(e))
                        logger.warning(f"Error de validación de foto: {e}", exc_info=True)
                        return render(request, 'autenticacion/registro.html', contexto) # Detener el proceso
                    
                    except GoogleCloudError as e:
                        # ¡Este es el error de configuración o permisos!
                        messages.error(request, "Error de servicio de archivos. Inténtalo de nuevo.")
                        logger.error(f"Error subiendo a GCP: {e}", exc_info=True)
                        # Aquí puedes decidir si quieres que el usuario continúe sin foto, o detener.
                        # Por simplicidad, asumiremos que detienes el registro.


                nivel = form.cleaned_data.get('nivel_educacional')
                institucion = form.cleaned_data.get('institucion')
                genero = form.cleaned_data.get('genero')

                if genero:
                    user.genero = genero

                if nivel:
                    user.n_educacion = nivel

                if institucion:
                    user.institucion = institucion

                user.save()

                # Asignar rol estudiante
                rol_estudiante = Rol.objects.get(nombre="Estudiante")
                user.roles.add(rol_estudiante)

                # Enviar correo de verificación
                enviar_verificacion_email_task.delay(user.id)

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

def obtener_comunas(request, region_id):
    try:
        comunas = Comuna.objects.filter(region_id=region_id).values('id', 'nombre')
        return JsonResponse(list(comunas), safe=False)
    except Exception as e:
        print("Error en obtener_comunas:", e)
        return JsonResponse({"error": str(e)}, status=500)