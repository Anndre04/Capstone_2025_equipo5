import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from .models import Evaluacion, Pregunta, Respuesta, EvaluacionPregunta, Tutoria, TipoPregunta, TipoEvaluacion, RealizacionRespuesta, Realizacion
from django.contrib import messages
from tutoria.models import Tutoria
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

logger = logging.getLogger(__name__)

@login_required
def crear_evaluacion(request, tutoria_id):    

    # --- CAMBIO CLAVE: Obtener el ÚNICO Tipo de Evaluación ---
    try:
        # Usa .first() para obtener el primer TipoEvaluacion, si existe alguno.
        tipo_evaluacion = TipoEvaluacion.objects.first() 
        if not tipo_evaluacion:
            return JsonResponse({'status': 'error', 'message': 'No existe ningún TipoEvaluacion definido.'}, status=500)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error al obtener TipoEvaluacion: {str(e)}'}, status=500)

    try:
        tipo_simple = TipoPregunta.objects.get(nombre="Selección simple")
    except TipoPregunta.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Tipo de Pregunta "Selección simple" no encontrado.'}, status=400)
    
    try:
        tutoria = Tutoria.objects.get(id=tutoria_id)
    except Tutoria.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Tutoría no encontrada.'}, status=404)
        
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    logger.info(f"📌 POST recibido para crear evaluación en tutoría: {tutoria_id}")

    try:
        with transaction.atomic():
            # --- USO: Asignar el tipo de evaluación obtenido ---
            evaluacion = Evaluacion.objects.create(
                titulo=request.POST['titulo'],
                tutoria=tutoria,
                tipo_evaluacion=tipo_evaluacion # Asigna el objeto obtenido
            )
            logger.info(f"✅ Evaluación creada: {evaluacion.id} con tipo: {tipo_evaluacion.nombre}")

            pregunta_index = 0
            total_puntos = 0

            while f'pregunta_{pregunta_index+1}' in request.POST:
                contenido = request.POST[f'pregunta_{pregunta_index+1}'].strip()
                puntos = int(request.POST.get(f'pregunta_{pregunta_index+1}_puntos', 1))

                total_puntos += puntos

                pregunta = Pregunta.objects.create(
                    contenido=contenido,
                    tipo=tipo_simple
                )
                logger.info(f"Pregunta creada: {pregunta.id} - {contenido}")

                opcion_index = 0
                while f'pregunta_{pregunta_index+1}_opcion_{opcion_index+1}' in request.POST:
                    op_text = request.POST[f'pregunta_{pregunta_index+1}_opcion_{opcion_index+1}'].strip()
                    correcta = int(request.POST.get(f'pregunta_{pregunta_index+1}_correcta', -1)) 
                    Respuesta.objects.create(
                        pregunta=pregunta,
                        contenido=op_text,
                        correcto=(opcion_index+1 == correcta)
                    )
                    logger.info(f"Opción creada: {op_text} (correcta: {opcion_index+1 == correcta})")
                    opcion_index += 1

                EvaluacionPregunta.objects.create(
                    evaluacion=evaluacion,
                    pregunta=pregunta,
                    puntos=puntos # Asigna el puntaje aquí
                )

                pregunta_index += 1

            evaluacion.puntaje_total = total_puntos
            evaluacion.estado = evaluacion.Estados.PUBLICADA
            evaluacion.save()

            # 1. Obtener la capa de canales
            channel_layer = get_channel_layer()

            # 2. Definir el nombre del grupo (debe coincidir con el nombre de tu sala de tutoría)
            # Ejemplo: si tu sala se llama 'tutoria_UUID', usa ese formato.
            room_group_name = f'tutoria_{evaluacion.tutoria.id}'

            # 3. Enviar el evento 'evaluacion_publicada'
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'evaluacion_publicada', # Nombre de la función en el consumer (ver paso 2)
                    'evaluacion_id': str(evaluacion.id), # Enviamos el ID necesario para construir el enlace
                }
            )

            logger.info(f"💯 Puntaje total guardado: {total_puntos}")

        return JsonResponse({'status': 'success', 'message': 'Se ha creado la evaluación'})
    
    except Exception as e:
        logger.exception(f"❌ Error al crear evaluación: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Hubo un error al crear la evaluación'})

@login_required
def responder_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id)
    estudiante = request.user # Asume que request.user es el objeto Usuario

    # --- CAMBIO CLAVE 1: Comprobar la existencia de la Realización (Intento Único) ---
    # Usamos la restricción unique_together para asegurar que solo haya un intento.
    try:
        realizacion = Realizacion.objects.get(evaluacion=evaluacion, estudiante=estudiante)
        # Si ya existe, significa que el estudiante ya respondió o está viendo su resultado.
        ya_respondio = True
        
    except Realizacion.DoesNotExist:
        # Si no existe, aún no ha respondido.
        realizacion = None
        ya_respondio = False


    # Obtener las preguntas que componen la evaluación (estructura estática)
    # Usamos EvaluacionPregunta para obtener las Preguntas y sus puntos.
    eval_preguntas = EvaluacionPregunta.objects.filter(evaluacion=evaluacion).select_related('pregunta')

    if not eval_preguntas.exists():
        # La evaluación está vacía (no tiene preguntas definidas).
        return redirect('home') 

    # --- Lógica POST: Guardar el nuevo intento/realización ---
    if request.method == 'POST':
        if ya_respondio:
            # Si el modelo Realizacion tiene unique_together, no permitimos un segundo POST.
            return HttpResponse("Ya has enviado esta evaluación.", status=403) 

        total_puntos_obtenidos = 0
        respuestas_a_crear = []

        try:
            with transaction.atomic():
                # --- CAMBIO CLAVE 2: Crear el registro de la Realización ---
                # Creamos el intento/realización. Fallará si ya existe por la restricción unique_together.
                realizacion = Realizacion.objects.create(
                    evaluacion=evaluacion, 
                    estudiante=estudiante,
                    puntaje_obtenido_total=0 # Se actualizará al final
                )
                logger.info(f"Realización creada para {estudiante}: {realizacion.id}")

                for ep in eval_preguntas:
                    pregunta = ep.pregunta
                    respuesta_id = request.POST.get(f'respuesta_{pregunta.id}')
                    
                    if respuesta_id:
                        respuesta_seleccionada = get_object_or_404(Respuesta, id=respuesta_id)
                        puntaje_obtenido = 0

                        # --- CAMBIO 3: Calcular puntaje basado en EvaluacionPregunta.puntos ---
                        if respuesta_seleccionada.correcto:
                            # Se usa ep.puntos (el puntaje definido para esta pregunta en esta evaluación)
                            puntaje_obtenido = ep.puntos 
                            total_puntos_obtenidos += puntaje_obtenido
                        
                        # --- CAMBIO 4: Acumular objetos RealizacionRespuesta para bulk_create o create ---
                        # Creamos el registro de la respuesta en el nuevo modelo:
                        respuestas_a_crear.append(RealizacionRespuesta(
                            realizacion=realizacion,
                            pregunta=pregunta,
                            respuesta_seleccionada=respuesta_seleccionada,
                            puntaje_obtenido=puntaje_obtenido
                        ))
                
                # Guardar todas las respuestas de una vez (opcional, pero más eficiente)
                RealizacionRespuesta.objects.bulk_create(respuestas_a_crear)

                # --- CAMBIO 5: Actualizar el puntaje total en el objeto Realizacion ---
                realizacion.puntaje_obtenido_total = total_puntos_obtenidos
                realizacion.save()

            return redirect('resultados_evaluacion', realizacion_id=realizacion.id) 

        except IntegrityError:
            logger.error("Intento duplicado detectado (Realizacion ya existe).")
            return HttpResponse("Error: Ya has enviado tu respuesta para esta evaluación.", status=409)
        except Exception as e:
            logger.exception("Error al guardar la realización de la evaluación.")
            return HttpResponse(f"Error interno: {str(e)}", status=500)


    # --- Lógica GET: Mostrar el formulario o el resultado si ya se respondió ---
    
    preguntas_con_opciones = []
    
    if ya_respondio:
        # Si ya respondió, cargamos sus respuestas para mostrarlas.
        respuestas_dadas = realizacion.respuestas_dadas.select_related('respuesta_seleccionada').all()
        respuestas_dict = {rr.pregunta.id: rr for rr in respuestas_dadas}
    else:
        respuestas_dict = {}

    for ep in eval_preguntas:
        pregunta = ep.pregunta
        respuestas_pregunta = respuestas_dict.get(pregunta.id)
        
        # Obtener la respuesta seleccionada y si es correcta
        seleccionada = respuestas_pregunta.respuesta_seleccionada if respuestas_pregunta else None
        
        preguntas_con_opciones.append({
            'evaluacion_pregunta': ep,
            'opciones': pregunta.respuestas.all(), # Obtener todas las opciones de Respuesta
            'seleccionada': seleccionada,
            'puntaje_obtenido': respuestas_pregunta.puntaje_obtenido if respuestas_pregunta else None,
            # Se usa el modelo RealizacionRespuesta para el puntaje y la selección
        })

    return render(request, 'responder.html', {
        'evaluacion': evaluacion,
        'preguntas_con_opciones': preguntas_con_opciones,
        'ya_respondio': ya_respondio,
        'realizacion': realizacion
    })

def resultados_evaluacion(request, realizacion_id):
    evaluacion_realizada = get_object_or_404(Realizacion, id=realizacion_id)

    contexto = {
        'evaluacion_realizada' : evaluacion_realizada
    }

    return render(request, 'resultadosevaluacion.html', contexto)