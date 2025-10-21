from django.shortcuts import get_object_or_404, render, redirect
from .models import Evaluacion, Pregunta, Respuesta, EvaluacionPregunta
from tutoria.models import Tutoria

#@login_required
def crear_evaluacion(request, tutoria_id):
    tutoria = Tutoria.objects.get(id=tutoria_id)

    if request.method == 'POST':
        # Crear Evaluación
        evaluacion = Evaluacion.objects.create(
            titulo=request.POST['titulo'],
            tutoria=tutoria
        )

        # Procesar preguntas
        pregunta_index = 0
        while f'pregunta_{pregunta_index}' in request.POST:
            contenido = request.POST[f'pregunta_{pregunta_index}']
            puntos = int(request.POST.get(f'pregunta_{pregunta_index}_puntos', 1))

            # Crear pregunta
            pregunta = Pregunta.objects.create(
                contenido=contenido,
                puntos=puntos,
                tipo_id=1  # Selección única
            )

            # Crear respuestas
            opcion_index = 0
            while f'pregunta_{pregunta_index}_op_{opcion_index}' in request.POST:
                op_text = request.POST[f'pregunta_{pregunta_index}_op_{opcion_index}']
                correcta = int(request.POST.get(f'pregunta_{pregunta_index}_correcta', -1))
                Respuesta.objects.create(
                    pregunta=pregunta,
                    contenido=op_text,
                    correcto=(opcion_index == correcta)
                )
                opcion_index += 1

            EvaluacionPregunta.objects.create(
                evaluacion=evaluacion,
                pregunta=pregunta,
                estudiante=tutoria.estudiante
            )

            pregunta_index += 1

        #return redirect('alguna_vista')  # redirige a donde quieras

    return render(request, 'crearevaluacion.html', {'tutoria': tutoria})




def responder_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id)
    
    eval_preguntas = EvaluacionPregunta.objects.filter(
        evaluacion=evaluacion,
        estudiante=request.user
    )

    if not eval_preguntas.exists():
        return redirect('home')  # o mostrar mensaje de error

    if request.method == 'POST':
        for ep in eval_preguntas:
            respuesta_id = request.POST.get(f'respuesta_{ep.pregunta.id}')
            if respuesta_id:
                ep.respuesta_seleccionada_id = respuesta_id
                
                # Calcular puntaje
                if ep.respuesta_seleccionada.correcto:
                    ep.puntaje_obtenido = ep.pregunta.puntos
                else:
                    ep.puntaje_obtenido = 0
                
                ep.save()

    # Preparar datos para mostrar en el template
    preguntas_con_opciones = []
    for ep in eval_preguntas:
        preguntas_con_opciones.append({
            'evaluacion_pregunta': ep,
            'opciones': ep.pregunta.respuestas.all(),
            'seleccionada': ep.respuesta_seleccionada,
            'correcta': ep.respuesta_seleccionada.correcto if ep.respuesta_seleccionada else None
        })

    return render(request, 'responder.html', {
        'evaluacion': evaluacion,
        'preguntas_con_opciones': preguntas_con_opciones,
    })

