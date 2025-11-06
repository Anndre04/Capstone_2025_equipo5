import os
import json
import uuid
import asyncio 
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from tutoria.models import Tutoria

# NOTA: Quité las importaciones de NumPy, CV2, VideoFrame, etc., que ya no se usan.

@login_required
def index(request, tutoria_id):
    tutoria = get_object_or_404(Tutoria, id=tutoria_id)

    # Validación: solo el tutor o estudiante puede acceder
    if request.user != tutoria.tutor.usuario and request.user != tutoria.estudiante:
        return render(request, "acceso_denegado.html", {
            "mensaje": "No tienes permiso para acceder a esta videollamada."
        })

    return render(request, "index.html", {"tutoria": tutoria})

PCS = set()
GRABACIONES_ACTIVAS = {} 

@csrf_exempt
async def iniciar_grabacion(request, tutoria_id):
    """
    Inicia la grabación recibiendo UN track de video compuesto (del Canvas) 
    y UN track de audio mezclado (de Web Audio API).
    """
    if tutoria_id in GRABACIONES_ACTIVAS:
        return JsonResponse({"status": "grabacion ya activa"}, status=409)

    try:
        data = json.loads(request.body)
        offer_sdp = data["sdp"]
    except json.JSONDecodeError:
        return HttpResponseBadRequest("SDP no proporcionado o JSON inválido.")

    pc = RTCPeerConnection()
    
    filename = f"grabaciones/{tutoria_id}_{uuid.uuid4()}.webm"
    os.makedirs("grabaciones", exist_ok=True)
    
    # 🌟 El recorder recibe el stream limpio
    recorder = MediaRecorder(filename)
    
    tracks_received = 0

    # --- Manejo de tracks entrantes simplificado ---
    @pc.on("track")
    async def on_track(track):
        nonlocal tracks_received
        # El cliente envía 1 video (canvas) y 1 audio (mezclado). Solo necesitamos añadirlos.
        recorder.addTrack(track)
        tracks_received += 1
        print(f"Track de {track.kind} añadido al recorder. Tracks recibidos: {tracks_received}")

    try:

        data = json.loads(request.body)
        offer = data.get("sdp")

        # Si 'offer' es un dict con 'sdp' y 'type', lo usamos directamente
        if isinstance(offer, dict):
            sdp = offer.get("sdp")
            sdp_type = offer.get("type", "offer")
        else:
            sdp = offer
            sdp_type = "offer"

        await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=sdp_type))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        # Esperar un poco para asegurar que los dos tracks se reciban antes de iniciar
        await asyncio.sleep(1.5) 

        # Si no se recibieron ambos tracks, podría haber un problema en el cliente.
        if tracks_received < 2:
             print(f"ADVERTENCIA: Solo se recibieron {tracks_received} tracks. Iniciando grabación...")

        await recorder.start()

        # --- Almacenar la sesión por ID de tutoría ---
        GRABACIONES_ACTIVAS[tutoria_id] = {
            "pc": pc,
            "recorder": recorder,
            "filename": filename,
            # Ya NO guardamos "video_composer"
        }

        return JsonResponse({
            "type": pc.localDescription.type,
            "sdp": pc.localDescription.sdp,
            "filename": filename
        })


    except Exception as e:
        print(f"Error durante la conexión/grabación: {e}")
        # Limpieza en caso de fallo
        if recorder: await recorder.stop()
        if pc: await pc.close()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
async def detener_grabacion(request, tutoria_id):
    if tutoria_id not in GRABACIONES_ACTIVAS:
        return JsonResponse({"status": "no habia grabacion activa para esta tutoria"}, status=404)

    sesion = GRABACIONES_ACTIVAS[tutoria_id]
    pc = sesion["pc"]
    recorder = sesion["recorder"]
    # El composer ya no existe

    # Detener y liberar recursos
    await recorder.stop()
    await pc.close()
    
    filename = sesion["filename"]
    del GRABACIONES_ACTIVAS[tutoria_id]

    return JsonResponse({"status": "grabacion guardada", "filename": filename})