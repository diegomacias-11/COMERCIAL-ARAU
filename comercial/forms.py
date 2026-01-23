from django import forms
from django.utils import timezone

from .models import ComercialKpi, ComercialKpiMeta, MES_CHOICES


class ComercialKpiForm(forms.ModelForm):
    class Meta:
        model = ComercialKpi
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre del KPI"}),
            "descripcion": forms.TextInput(attrs={"placeholder": "Descripción"}),
        }


class ComercialKpiMetaForm(forms.ModelForm):
    anio = forms.IntegerField(
        label="Año",
        widget=forms.NumberInput(attrs={"min": 2000, "step": 1}),
    )
    mes = forms.TypedChoiceField(choices=MES_CHOICES, coerce=int, label="Mes")

    class Meta:
        model = ComercialKpiMeta
        fields = ["kpi", "mes", "anio", "meta"]

    def __init__(self, *args, filter_month=None, filter_year=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("anio") and not getattr(self.instance, "anio", None):
            self.initial["anio"] = timezone.now().year
        if filter_month and filter_year:
            used = ComercialKpiMeta.objects.filter(mes=filter_month, anio=filter_year)
            if self.instance and self.instance.pk:
                used = used.exclude(pk=self.instance.pk)
            used_ids = used.values_list("kpi_id", flat=True)
            self.fields["kpi"].queryset = ComercialKpi.objects.exclude(id__in=used_ids)
