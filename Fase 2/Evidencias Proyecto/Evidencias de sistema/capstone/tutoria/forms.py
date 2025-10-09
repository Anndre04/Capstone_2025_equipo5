from django import forms
from autenticacion.models import AreaInteres
from .models import Archivo

# Widget que permite subir varios archivos
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class TutorRegistrationForm(forms.Form):
    areas = forms.MultipleChoiceField(
        label='Áreas de Conocimiento',
        widget=forms.CheckboxSelectMultiple
    )

    certificacion = forms.FileField(
        label='Subir certificación (PDF)',
        required=True   # Por defecto FileField es obligatorio
    )

    # Cargamos las áreas desde el modelo
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['areas'].choices = [
            (area.id, area.nombre) for area in AreaInteres.objects.all()
        ]
