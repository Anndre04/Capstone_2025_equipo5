import base64

def usuarioFoto(request):
    if request.user.is_authenticated and request.user.foto:
        foto_bytes = bytes(request.user.foto)
        foto_base64 = base64.b64encode(foto_bytes).decode('utf-8')
        return {"foto_base64": foto_base64}
    return {"foto_base64": None}