# chat/filters.py
import re
import logging

logger = logging.getLogger(__name__)

class FiltroLenguajeChileno:
    def __init__(self):
        self.palabras_prohibidas = {
            'aweonao', 'ahueonao', 'aweona', 'ahueona', 'ahuevonada', 'awuevonada','puta', 'puto', 'maricon', 'maricón', 'marica', 'culiao', 'culiado',
            'conchetumare', 'ctm', 'ktm','wea', 'huea', 'pico', 'pene', 'verga',
            'mierda', 'carajo', 'caraca', 'chucha'
        }
        
    def filtrar_mensaje(self, mensaje):
        mensaje_original = mensaje
        mensaje_min = mensaje.lower()
        
        # Verificar palabras prohibidas
        palabras = re.findall(r'\b\w+\b', mensaje_min)
        for palabra in palabras:
            logger.warning(f"Palabra prohibida detectada: {palabra}")
            raise ValueError("El mensaje contiene lenguaje inapropiado")
        

# Instancia global
filtro_lenguaje = FiltroLenguajeChileno()