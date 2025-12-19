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
            "fecha_fin",
            "tarea",
            "dias",
            "mercadologo",
            "disenador",
            "evaluacion",
        ]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
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

        if self.user and self.user.is_authenticated:
            first = (self.user.first_name or "").strip().split(" ")[0].lower()
            is_dir = self.user.groups.filter(name__iexact="Dirección Marketing").exists()
            is_mkt = self.user.groups.filter(name__iexact="Marketing").exists()
            is_dsn = self.user.groups.filter(name__iexact="Diseño").exists()

            if is_mkt and not is_dir and "mercadologo" in self.fields:
                opciones = [(v, l) for v, l in self.fields["mercadologo"].choices if v.lower().startswith(first)]
                if opciones:
                    self.fields["mercadologo"].choices = opciones
                    self.fields["mercadologo"].initial = opciones[0][0]
                self.fields["mercadologo"].disabled = True
                if "disenador" in self.fields:
                    self.fields["disenador"].disabled = True
                    self.fields["disenador"].required = False

            if is_dsn and not is_dir and "disenador" in self.fields:
                opciones = [(v, l) for v, l in self.fields["disenador"].choices if v.lower().startswith(first)]
                if opciones:
                    self.fields["disenador"].choices = opciones
                    self.fields["disenador"].initial = opciones[0][0]
                self.fields["disenador"].disabled = True
                if "mercadologo" in self.fields:
                    self.fields["mercadologo"].disabled = True
                    self.fields["mercadologo"].required = False

            if (is_mkt or is_dsn) and not is_dir and self.instance and getattr(self.instance, "pk", None):
                for fname, field in self.fields.items():
                    if fname != "fecha_fin":
                        field.disabled = True
