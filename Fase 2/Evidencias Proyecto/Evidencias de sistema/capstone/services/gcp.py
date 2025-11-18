import logging
import mimetypes
import os
from google.cloud import storage
from django.conf import settings
from datetime import timedelta

logger = logging.getLogger(__name__)

def get_bucket():
    """Retorna el bucket GCP sin inicializar nada en models.py."""
    client = storage.Client.from_service_account_json(settings.GOOGLE_APPLICATION_CREDENTIALS)
    return client.bucket(settings.GOOGLE_CLOUD_BUCKET)

def generar_url_firmada(ruta_gcs, expiracion_segundos=3600, descargar=False):
    """Genera URL firmada para un objeto en GCS."""
    try:
        ruta_gcs_str = str(ruta_gcs).strip()
        bucket = get_bucket()
        blob = bucket.blob(ruta_gcs_str)
        disposition = "attachment" if descargar else "inline"

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiracion_segundos),
            method="GET",
            response_disposition=f"{disposition}; filename={os.path.basename(ruta_gcs_str)}"
        )
        return url
    except Exception as e:
        logger.error(f"Error generando URL firmada para {ruta_gcs}: {e}", exc_info=True)
        return None

def subir_archivo_gcp(archivo, nombre, tutor_id=None, tutoria_id=None):
    """
    Sube un archivo a GCS. Sobrescribe si ya existe.
    Solo se debe pasar tutor_id O tutoria_id, no ambos.
    """
    if not archivo:
        logger.warning("No se proporcionó archivo para subir a GCS.")
        return None

    # Validar que no se pasen ambos IDs
    if tutor_id and tutoria_id:
        logger.error("Se recibió tutor_id y tutoria_id juntos. Solo uno debe estar presente.")
        return None

    if tutor_id:
        directorio_base = f'PDFs/certificaciones/tutor_{tutor_id}'
        logger.debug(f"Ruta para certificación (Tutor ID: {tutor_id})")
    elif tutoria_id:
        directorio_base = f'PDFs/Archivos_tutoria/tutoria_{tutoria_id}'
        logger.debug(f"Ruta para archivo de tutoria (Tutoria ID: {tutoria_id})")
    else:
        logger.error("Se requiere tutor_id o tutoria_id para subir archivo.")
        return None

    try:
        bucket = get_bucket()
        nombre_seguro = os.path.basename(nombre)
        ruta_destino_gcs = f'{directorio_base}/{nombre_seguro}'
        blob = bucket.blob(ruta_destino_gcs)
        content_type = mimetypes.guess_type(archivo.name)[0] or 'application/octet-stream'

        blob.upload_from_file(archivo, content_type=content_type)
        logger.info(f"Archivo subido a GCS: {ruta_destino_gcs} (MIME: {content_type})")
        archivo.seek(0)
        return ruta_destino_gcs
    except Exception as e:
        logger.error(f"Error subiendo {archivo.name} a GCS: {e}", exc_info=True)
        return None

def subir_foto_perfil_gcp(archivo, email_usuario, carpeta='fotos_perfil'):
    """
    Sube una foto de perfil a GCP.
    Si ya existía una foto anterior para ese usuario, se elimina.
    Retorna la ruta relativa del nuevo archivo.
    """
    if not archivo:
        logger.warning("No se proporcionó archivo para subir foto de perfil.")
        return None

    try:
        bucket = get_bucket()
        nombre_base = f"{carpeta}/{email_usuario}"

        # 1️⃣ Buscar y eliminar fotos anteriores
        blobs_existentes = bucket.list_blobs(prefix=nombre_base)
        for blob in blobs_existentes:
            try:
                blob.delete()
                logger.debug(f"Foto previa eliminada: {blob.name}")
            except Exception as e:
                logger.error(f"No se pudo eliminar el archivo {blob.name}: {e}", exc_info=True)

        # 2️⃣ Construir nombre del nuevo archivo
        extension = archivo.name.split('.')[-1]
        nombre_nuevo = f"{nombre_base}.{extension}"
        blob_nuevo = bucket.blob(nombre_nuevo)

        # 3️⃣ Subir el archivo
        content_type = getattr(archivo, 'content_type', 'application/octet-stream')
        blob_nuevo.upload_from_file(archivo, content_type=content_type)
        logger.info(f"Foto de perfil subida a GCP: {nombre_nuevo}")

        archivo.seek(0)  # Resetear puntero
        return nombre_nuevo

    except Exception as e:
        logger.error(f"Error subiendo foto de perfil para {email_usuario}: {e}", exc_info=True)
        return None
