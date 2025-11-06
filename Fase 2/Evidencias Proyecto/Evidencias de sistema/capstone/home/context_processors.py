import base64
import imghdr
from django.db.models import Q 
from tutoria.models import Tutoria

'''def usuario_foto(request):
    if request.user.is_authenticated and request.user.foto:
        foto_bytes = bytes(request.user.foto)
        # Obtener tipo MIME de la extensión original si lo tienes
        # Por ejemplo, asumir PNG si no lo sabes:
        mime_type = 'image/jpg'  # o 'image/jpeg', según lo que permitas
        foto_base64 = base64.b64encode(foto_bytes).decode('utf-8')
        return {"foto_base64": foto_base64, "foto_mime": mime_type}
    return {"foto_base64": None, "foto_mime": None}
'''

def tutoriaEnCurso(request):
    if request.user.is_authenticated:
        tutoria = Tutoria.objects.filter(
            Q(tutor__usuario=request.user) | Q(estudiante=request.user),
            estado="En curso"
        ).first()
        return {"tutoria_en_curso": tutoria}
    return {"tutoria_en_curso": None}