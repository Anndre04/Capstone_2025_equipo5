# forms.py
from django import forms

class TutorRegistrationForm(forms.Form):
    nombre = forms.CharField(label='Nombre completo', max_length=100)
    email = forms.EmailField(label='Correo electrónico')
    telefono = forms.CharField(label='Teléfono', max_length=15)
    areas = forms.MultipleChoiceField(
        label='Áreas de Conocimiento',
        choices=[
            ('Matemáticas', 'Matemáticas'),
            ('Física', 'Física'),
            ('Química', 'Química'),
            ('Programación', 'Programación'),
            ('Biología', 'Biología'),
            ('Historia', 'Historia')
        ],
        widget=forms.CheckboxSelectMultiple
    )
    certificaciones = forms.FileField(
        label='Subir certificaciones (PDF)',
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False
    )
    terminos = forms.BooleanField(label='Acepto los términos y condiciones', required=True)
