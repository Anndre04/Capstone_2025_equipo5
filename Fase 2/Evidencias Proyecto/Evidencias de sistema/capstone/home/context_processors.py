from django.db.models import Q 
from tutoria.models import Tutoria



def tutoriaEnCurso(request):
    if request.user.is_authenticated:
        tutoria = Tutoria.objects.filter(
            Q(tutor__usuario=request.user) | Q(estudiante=request.user),
            estado="En curso"
        ).first()
        return {"tutoria_en_curso": tutoria}
    return {"tutoria_en_curso": None} #agregado para evitar errores cuando no hay usuario autenticado