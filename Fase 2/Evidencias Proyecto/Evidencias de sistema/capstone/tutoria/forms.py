from django import forms
from django.core.exceptions import ValidationError
from autenticacion.models import AreaInteres
from .models import Archivo

# Widget que soporta múltiples archivos
class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class TutorRegistrationForm(forms.Form):
    areas = forms.MultipleChoiceField(
        label='Áreas de Conocimiento',
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['areas'].choices = [
            (area.id, area.nombre) for area in AreaInteres.objects.all()
        ]