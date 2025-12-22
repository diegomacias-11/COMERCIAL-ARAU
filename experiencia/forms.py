from django import forms

from .models import ExperienciaCliente


class ExperienciaClienteForm(forms.ModelForm):
    class Meta:
        model = ExperienciaCliente
        fields = [
            "nombre_comercial",
            "domicilio",
            "puesto",
            "fecha_contrato",
            "periodicidad",
            "chat_welcome",
            "meet",
            "comentarios",
        ]
        widgets = {
            "fecha_contrato": forms.DateInput(attrs={"type": "date"}),
            "comentarios": forms.Textarea(attrs={"rows": 3}),
        }
