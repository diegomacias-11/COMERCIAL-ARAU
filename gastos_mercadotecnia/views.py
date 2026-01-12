from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import GastoMercadotecnia

class GastoMercadotecniaForm(forms.ModelForm):
    class Meta:
        model = GastoMercadotecnia
        fields = [
            "fecha_facturacion",
            "categoria",
            "plataforma",
            "marca",
            "tdc",
            "tipo_facturacion",
            "periodicidad",
            "facturacion",
            "notas",
        ]
        widgets = {
            "fecha_facturacion": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("categoria", "plataforma", "marca", "tdc", "tipo_facturacion", "periodicidad"):
            if name in self.fields:
                choices = list(self.fields[name].choices)
                self.fields[name].choices = [("", "----")] + choices


def gastos_lista(request):
    gastos = GastoMercadotecnia.objects.all().order_by("-fecha_facturacion", "-creado")
    return render(request, "gastos_mercadotecnia/lista.html", {"gastos": gastos})


def gastos_crear(request):
    back_url = request.GET.get("next") or reverse("gastos_mercadotecnia_gasto_list")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = GastoMercadotecniaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = GastoMercadotecniaForm()
    return render(request, "gastos_mercadotecnia/form.html", {"form": form, "back_url": back_url})


def gastos_editar(request, pk: int):
    gasto = get_object_or_404(GastoMercadotecnia, pk=pk)
    back_url = request.GET.get("next") or reverse("gastos_mercadotecnia_gasto_list")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = GastoMercadotecniaForm(request.POST, instance=gasto)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = GastoMercadotecniaForm(instance=gasto)
    return render(request, "gastos_mercadotecnia/form.html", {"form": form, "back_url": back_url, "gasto": gasto})
