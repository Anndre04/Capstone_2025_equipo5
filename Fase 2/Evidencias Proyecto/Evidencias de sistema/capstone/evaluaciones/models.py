import uuid
from django.db import models
from django.db.models import Sum
from autenticacion.models import Usuario 
from tutoria.models import Tutoria 

# --------------------------------------------------------------------------
# 1. CLASIFICACIÓN (TIPOS)
# --------------------------------------------------------------------------

class TipoPregunta(models.Model):
    """Define la clasificación de la pregunta (e.g., Opción Múltiple, Abierta)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class TipoEvaluacion(models.Model):
    """
    Define el propósito pedagógico de la evaluación (e.g., Diagnóstica, Formativa, Sumativa).
    Esto permite filtrar y aplicar reglas de negocio específicas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True, null=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


# --------------------------------------------------------------------------
# 2. BANCO DE PREGUNTAS Y RESPUESTAS (Contenido Estático)
# --------------------------------------------------------------------------

class Pregunta(models.Model):
    """
    Representa el banco o catálogo de preguntas.
    El campo 'puntos' se ha movido para soportar la valoración dinámica por evaluación.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contenido = models.CharField(max_length=500)
    tipo = models.ForeignKey(TipoPregunta, on_delete=models.PROTECT, related_name='preguntas')

    def __str__(self):
        return self.contenido

class Respuesta(models.Model):
    """
    Representa una opción de respuesta asociada a una Pregunta.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pregunta = models.ForeignKey(
        Pregunta, 
        on_delete=models.PROTECT, 
        related_name='respuestas'
    )
    contenido = models.CharField(max_length=250)
    correcto = models.BooleanField(default=False) 

    def __str__(self):
        return self.contenido


# --------------------------------------------------------------------------
# 3. DEFINICIÓN DE LA EVALUACIÓN (Estructura Estática y Valoración Dinámica)
# --------------------------------------------------------------------------

class Evaluacion(models.Model):
    """Define la prueba o examen."""

    # 💡 MEJORA: Usar TextChoices (la forma recomendada por Django)
    class Estados(models.TextChoices):
        # Valor de la Base de Datos | Nombre legible para el usuario/Admin
        BORRADOR = 'BORRADOR', 'Borrador (Edición)'
        PUBLICADA = 'PUBLICADA', 'Habilitada (Lista para responder)'
        CERRADA = 'CERRADA', 'Cerrada (No se aceptan más respuestas)'
        ARCHIVADA = 'ARCHIVADA', 'Archivada (Histórica)'
        ELIMINADA = 'ELIMINADA', 'Se eliminó antes de respondida'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=100)
    fecha_creacion = models.DateField(auto_now_add=True)
    preguntas = models.ManyToManyField(Pregunta, through='EvaluacionPregunta')
    tutoria = models.ForeignKey(
        Tutoria, # Asume que existe un modelo 'Tutoria'
        on_delete=models.PROTECT,
        related_name='evaluaciones'
    )
    tipo_evaluacion = models.ForeignKey(
        TipoEvaluacion, 
        on_delete=models.PROTECT, 
        related_name='evaluaciones'
    )     
    # Definición del campo estado usando TextChoices
    estado = models.CharField(
        max_length=10, 
        choices=Estados.choices,
        default=Estados.BORRADOR # Establece un valor inicial
    )

    puntaje_total = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        # Sincroniza el total solo si está en estado Borrador (donde es editable)
        if self.estado == Evaluacion.Estados.BORRADOR:
            # Calcular el total de puntos de las preguntas asociadas
            # Nota: Esto solo funciona si se llama DESPUÉS de guardar las EvaluacionPregunta
            resultado = self.evaluacion_preguntas.aggregate(total=Sum('puntos'))
            self.puntaje_total = resultado.get('total') or 0
            
        super().save(*args, **kwargs)

    def __str__(self):
        # Usa get_estado_display() para mostrar el nombre legible
        return f"Evaluación {self.titulo} ({self.get_estado_display()})"

class EvaluacionPregunta(models.Model):
    """
    TABLA INTERMEDIARIA: Define qué preguntas componen la Evaluación.
    Contiene el puntaje de la pregunta DENTRO del contexto de esta evaluación.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey(
        Evaluacion, 
        on_delete=models.PROTECT, 
        related_name='evaluacion_preguntas'
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT)
    
    # Puntaje dinámico: Permite que la misma pregunta valga diferente en distintas evaluaciones.
    puntos = models.IntegerField(default=1) 
    
    class Meta:
        # Asegura que una pregunta no se repita en la misma evaluación
        unique_together = ('evaluacion', 'pregunta')

    def __str__(self):
        return f"E: {self.evaluacion.titulo} - P: {self.pregunta.contenido[:30]}"


# --------------------------------------------------------------------------
# 4. REGISTRO DEL RESULTADO (Interacción Dinámica)
# --------------------------------------------------------------------------

class Realizacion(models.Model):
    """
    Representa la realización o el resultado final de una Evaluación por parte de un Estudiante.
    El nombre es escalable, aunque actualmente restringe a un único intento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante = models.ForeignKey(
        Usuario, # Asume que existe el modelo 'Usuario'
        on_delete=models.PROTECT,
        related_name='realizaciones'
    )
    evaluacion = models.ForeignKey(
        Evaluacion, 
        on_delete=models.PROTECT, 
        related_name='realizaciones'
    )
    
    # Campo para registrar la fecha del intento/realización.
    fecha_intento = models.DateTimeField(auto_now_add=True) 
    puntaje_obtenido_total = models.IntegerField(default=0) 

    class Meta:
        # REGLA DE NEGOCIO: Restringe a UN SOLO intento (Realizacion) por estudiante/evaluación.
        # Si se desea permitir múltiples intentos en el futuro, solo se elimina esta línea.
        unique_together = ('estudiante', 'evaluacion') 

    def __str__(self):
        return f"Realización de {self.estudiante} en {self.evaluacion.titulo}, {self.id}"


class RealizacionRespuesta(models.Model):
    """
    Registra la respuesta específica de UNA pregunta dentro de una Realización (intento).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Relación con la Realizacion (el contenedor del intento)
    realizacion = models.ForeignKey(
        Realizacion, 
        on_delete=models.PROTECT, 
        related_name='respuestas_dadas'
    )
    # Relación con la Pregunta original
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT)
    
    # La respuesta que el estudiante seleccionó
    respuesta_seleccionada = models.ForeignKey(
        Respuesta,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    puntaje_obtenido = models.IntegerField(default=0)
    
    class Meta:
        # Asegura que solo haya una respuesta por pregunta dentro de cada Realización.
        unique_together = ('realizacion', 'pregunta')

    @property
    def puntos_maximos(self):
        """Busca el valor de 'puntos' en EvaluacionPregunta (la tabla intermedia)."""
        # Accedemos a la Evaluación a través de la Realización.
        evaluacion_actual = self.realizacion.evaluacion
        pregunta_actual = self.pregunta
        
        # Filtramos la tabla intermedia (EvaluacionPregunta)
        ep = EvaluacionPregunta.objects.filter(
            evaluacion=evaluacion_actual,
            pregunta=pregunta_actual
        ).first()
        
        # Devolvemos el campo 'puntos' si se encuentra.
        return ep.puntos if ep else 0

    def __str__(self):
        return f"Rta a {self.pregunta.contenido[:20]} en {self.realizacion.evaluacion.titulo}"