from django import forms

from .models import ExperienciaCliente


class ExperienciaClienteForm(forms.ModelForm):
    class Meta:
        model = ExperienciaCliente
        fields = [
            "nombre_comercial",
            "estatus",
            "domicilio",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "pk", None) and self.instance.fecha_contrato:
            self.initial["fecha_contrato"] = self.instance.fecha_contrato.isoformat()
