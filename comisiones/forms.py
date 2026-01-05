from django import forms

from .models import PagoComision, Comision


class PagoComisionForm(forms.ModelForm):
    comision = forms.ModelChoiceField(queryset=Comision.objects.none(), label="Pago comisión")

    class Meta:
        model = PagoComision
        fields = [
            "comision",
            "fecha_pago",
            "monto",
            "comentario",
        ]
        widgets = {
            "fecha_pago": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        comisiones_qs = kwargs.pop("comisiones_qs", None)
        super().__init__(*args, **kwargs)
        if comisiones_qs is not None:
            self.fields["comision"].queryset = comisiones_qs
        self.fields["comision"].empty_label = "---"
        self.fields["comision"].label_from_instance = lambda c: f"{getattr(c.cliente, 'cliente', c.cliente)} - {c.servicio}"

        self.fields["monto"].required = False
        self.fields["monto"].disabled = True
        self.fields["monto"].widget.attrs["readonly"] = True

        if self.instance and getattr(self.instance, "pk", None) and not self.is_bound:
            if self.instance.fecha_pago:
                self.initial["fecha_pago"] = self.instance.fecha_pago.isoformat()
            self.fields["comision"].initial = self.instance.comision_id
            self.fields["comision"].disabled = True
            self.initial["monto"] = self.instance.monto
