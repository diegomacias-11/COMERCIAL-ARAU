from calendar import monthrange

from django import forms

from .models import Venta


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = [
            "fecha",
            "cliente",
            "facturadora",
            "num_factura",
            "fecha_pago",
            "fecha_vigencia",
            "fecha_arranque",
            "monto_venta",
            "comentarios",
            "estatus_pago",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "fecha_pago": forms.DateInput(attrs={"type": "date"}),
            "fecha_vigencia": forms.DateInput(attrs={"type": "date"}),
            "fecha_arranque": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.mes = kwargs.pop("mes", None)
        self.anio = kwargs.pop("anio", None)
        super().__init__(*args, **kwargs)

        if "cliente" in self.fields:
            self.fields["cliente"].label_from_instance = (
                lambda obj: f"{getattr(obj, 'cliente', '')} - "
                f"{getattr(obj, 'get_servicio_display', lambda: getattr(obj, 'servicio', ''))()}"
            )

        if self.instance and getattr(self.instance, "pk", None):
            for fname in ("cliente", "monto_venta"):
                if fname in self.fields:
                    self.fields[fname].disabled = True
                    self.fields[fname].required = False
            if self.instance.fecha is not None:
                self.initial["fecha"] = self.instance.fecha.isoformat()
            for fname in ("fecha_pago", "fecha_vigencia", "fecha_arranque"):
                val = getattr(self.instance, fname, None)
                if val and fname in self.fields:
                    self.initial[fname] = val.isoformat()

        if self.mes and self.anio:
            first_day = f"{int(self.anio):04d}-{int(self.mes):02d}-01"
            last_dom = monthrange(int(self.anio), int(self.mes))[1]
            last_day = f"{int(self.anio):04d}-{int(self.mes):02d}-{last_dom:02d}"
            self.fields["fecha"].widget.attrs.update({"min": first_day, "max": last_day})
            if not self.initial.get("fecha") and not (self.instance and self.instance.pk):
                self.initial["fecha"] = first_day

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        if fecha and self.mes and self.anio:
            if fecha.month != int(self.mes) or fecha.year != int(self.anio):
                raise forms.ValidationError("La fecha debe pertenecer al mes filtrado.")
        return fecha
