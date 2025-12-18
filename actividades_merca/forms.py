from django import forms

from clientes.models import Cliente
from .models import ActividadMerca


EXTRA_CLIENTES = ["ARAU", "ENROK", "HUNTERLOOP", "W DESARROLLOS"]


def _cliente_choices():
    qs = (
        Cliente.objects.filter(servicio="Marketing")
        .order_by("cliente")
        .values_list("cliente", flat=True)
    )
    vistos = set()
    choices = []
    for nombre in EXTRA_CLIENTES:
        val = nombre.strip().upper()
        if val and val not in vistos:
            choices.append((val, val))
            vistos.add(val)
    for nombre in qs:
        val = (nombre or "").strip().upper()
        if val and val not in vistos:
            choices.append((val, val))
            vistos.add(val)
    return choices


class ActividadMercaForm(forms.ModelForm):
    class Meta:
        model = ActividadMerca
        fields = [
            "cliente",
            "area",
            "fecha_inicio",
            "tarea",
            "dias",
            "mercadologo",
            "disenador",
            "evaluacion",
        ]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"] = forms.ChoiceField(
            label="Cliente",
            choices=[("", "----")] + _cliente_choices(),
        )
        if self.instance and getattr(self.instance, "pk", None):
            if "fecha_inicio" in self.fields:
                self.fields["fecha_inicio"].disabled = True
                self.fields["fecha_inicio"].required = False
                if self.instance.fecha_inicio:
                    try:
                        self.initial["fecha_inicio"] = self.instance.fecha_inicio.strftime("%Y-%m-%d")
                    except Exception:
                        pass
        else:
            # Al crear, ocultar evaluacion (solo se usa en edición)
            self.fields.pop("evaluacion", None)
