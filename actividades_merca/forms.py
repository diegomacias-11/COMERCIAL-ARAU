from django import forms
import unicodedata

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
            if "cliente" in self.fields:
                self.initial["cliente"] = (self.instance.cliente or "").strip().upper()
            if "area" in self.fields:
                self.initial["area"] = self.instance.area or ""
            if "mercadologo" in self.fields:
                self.initial["mercadologo"] = self.instance.mercadologo or ""
            if "disenador" in self.fields:
                self.initial["disenador"] = self.instance.disenador or ""
            if "fecha_inicio" in self.fields:
                self.fields["fecha_inicio"].disabled = True
                self.fields["fecha_inicio"].required = False
                if self.instance.fecha_inicio:
                    try:
                        self.initial["fecha_inicio"] = self.instance.fecha_inicio.strftime("%Y-%m-%d")
                    except Exception:
                        pass
            if "fecha_fin" in self.fields:
                if self.instance.fecha_fin:
                    try:
                        self.initial["fecha_fin"] = self.instance.fecha_fin.strftime("%Y-%m-%d")
                    except Exception:
                        pass
                    # Una vez establecida no es editable
                    self.fields["fecha_fin"].disabled = True
                else:
                    # Editable mientras no tenga fecha fin
                    self.fields["fecha_fin"].disabled = False
            # Bloquear todo excepto tarea, dias, evaluacion y asignaciones
            for fname, field in self.fields.items():
                if fname not in {"tarea", "dias", "evaluacion", "mercadologo", "disenador", "fecha_fin"}:
                    field.disabled = True
        else:
            # Al crear, ocultar campos que solo se manejan en edición
            self.fields.pop("evaluacion", None)
            self.fields.pop("fecha_fin", None)

        if self.user and self.user.is_authenticated:
            first = (self.user.first_name or "").strip().split(" ")[0].lower()
            full_name = (self.user.get_full_name() or self.user.username or "").strip()
            group_names = [g.name for g in self.user.groups.all()]

            def _norm(name: str) -> str:
                value = unicodedata.normalize("NFKD", name or "")
                return "".join(ch for ch in value if not unicodedata.combining(ch)).lower().strip()

            normed = {_norm(name) for name in group_names}
            is_dir = "direccion marketing" in normed
            is_mkt = "marketing" in normed
            is_dsn = "diseno" in normed

            if is_mkt and not is_dir and "mercadologo" in self.fields:
                opciones = [(v, l) for v, l in self.fields["mercadologo"].choices if v.lower().startswith(first)]
                if opciones:
                    self.fields["mercadologo"].choices = opciones
                    self.fields["mercadologo"].initial = opciones[0][0]
                elif full_name:
                    self.fields["mercadologo"].choices = [(full_name, full_name)]
                    self.fields["mercadologo"].initial = full_name
                self.fields["mercadologo"].disabled = True
                if "disenador" in self.fields:
                    self.fields["disenador"].disabled = True
                    self.fields["disenador"].required = False

            if is_dsn and not is_dir and "disenador" in self.fields:
                opciones = [(v, l) for v, l in self.fields["disenador"].choices if v.lower().startswith(first)]
                if opciones:
                    self.fields["disenador"].choices = opciones
                    self.fields["disenador"].initial = opciones[0][0]
                elif full_name:
                    self.fields["disenador"].choices = [(full_name, full_name)]
                    self.fields["disenador"].initial = full_name
                self.fields["disenador"].disabled = True
                if "mercadologo" in self.fields:
                    self.fields["mercadologo"].disabled = True
                    self.fields["mercadologo"].required = False

            if (is_mkt or is_dsn) and not is_dir and self.instance and getattr(self.instance, "pk", None):
                for fname, field in self.fields.items():
                    if fname != "fecha_fin":
                        field.disabled = True
