import base64
from django.db.models import Q 
from tutoria.models import Tutoria

def usuarioFoto(request):
    if request.user.is_authenticated and request.user.foto:
        foto_bytes = bytes(request.user.foto)
        foto_base64 = base64.b64encode(foto_bytes).decode('utf-8')
        return {"foto_base64": foto_base64}
    return {"foto_base64": None}

def tutoriaEnCurso(request):
    if request.user.is_authenticated:
        tutoria = Tutoria.objects.filter(
            Q(tutor__usuario=request.user) | Q(estudiante=request.user),
            estado="En curso"
        ).first()
        return {"tutoria_en_curso": tutoria}
    return {"tutoria_en_curso": None}