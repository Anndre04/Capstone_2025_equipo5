from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def mistutoriasprof(request):
    return render(request, 'tutoria/mistutoriasprof.html')

@login_required
def anunciotutor(request):
    return render(request, 'tutoria/anunciotutor.html')

@login_required
def solicitudesprof(request):
    return render(request, 'tutoria/solicitudesprof.html')

@login_required
def gestortutorias(request):
    return render(request, 'tutoria/gestortutorias.html')
