from django import forms

from alianzas.models import Alianza
from .models import PagoComision


class PagoComisionForm(forms.ModelForm):
    comisionista = forms.ModelChoiceField(queryset=Alianza.objects.none())

    class Meta:
        model = PagoComision
        fields = [
            "comisionista",
            "fecha_pago",
            "monto",
            "comentario",
        ]
        widgets = {
            "fecha_pago": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "pk", None) and not self.is_bound:
            if self.instance.fecha_pago:
                self.initial["fecha_pago"] = self.instance.fecha_pago.isoformat()
