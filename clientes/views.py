from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, time

from .models import Cliente
from alianzas.models import Alianza


class ClienteForm(forms.ModelForm):
    comision_campos = [f"comision_{i}" for i in range(1, 11)]
    comisionista_campos = [f"comisionista_{i}" for i in range(1, 11)]

    class Meta:
        model = Cliente
        fields = [
            "cliente",
            "servicio",
            "giro",
            "tipo",
            "medio",
            "contacto",
            "telefono",
            "correo",
            "conexion",
            *[f"comisionista_{i}" for i in range(1, 11)],
            *[f"comision_{i}" for i in range(1, 11)],
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.update({
            campo: self.fields[campo]
            for campo in self.comisionista_campos + self.comision_campos
            if campo in self.fields
        })
        # Ordenar alianzas por nombre (ya guardadas en uppercase/strip)
        alianza_qs = Alianza.objects.all().order_by("nombre")
        for campo in self.comisionista_campos:
            self.fields[campo].queryset = alianza_qs
            self.fields[campo].label = f"Comisionista {campo.split('_')[-1]}"
        # Mostrar valores porcentuales como enteros
        for campo in self.comision_campos:
            self.fields[campo].widget = forms.NumberInput(attrs={"step": "0.01", "min": "0"})
            self.fields[campo].label = f"Comisión {campo.split('_')[-1]} (%)"
            if self.initial.get(campo) is not None:
                try:
                    self.initial[campo] = float(self.initial[campo]) * 100
                except Exception:
                    pass

        # Pasar fecha_registro para display en plantilla, igual que en comercial
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None) and self.instance.fecha_registro:
            self.fecha_registro_display = timezone.localtime(self.instance.fecha_registro)

    def clean(self):
        cleaned = super().clean()
        # Convertir porcentajes enteros a decimales (10 -> 0.10)
        for campo in self.comision_campos:
            val = cleaned.get(campo)
            if val is not None:
                cleaned[campo] = val / 100
        return cleaned


def _comision_pairs(form: ClienteForm):
    pairs = []
    for i in range(1, 11):
        ci = f"comisionista_{i}"
        cv = f"comision_{i}"
        if ci in form.fields and cv in form.fields:
            pairs.append((form[ci], form[cv]))
    return pairs


def clientes_lista(request):
    clientes = Cliente.objects.all().order_by("-fecha_registro")
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""

    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(d, time.min), tz)
            clientes = clientes.filter(fecha_registro__gte=start_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(d, time.max), tz)
            clientes = clientes.filter(fecha_registro__lte=end_dt)
        except ValueError:
            pass
    context = {
        "clientes": clientes,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    return render(request, "clientes/lista.html", context)


def agregar_cliente(request):
    back_url = request.GET.get("next") or reverse("clientes_lista")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ClienteForm()

    context = {"form": form, "back_url": back_url, "comisiones": _comision_pairs(form)}
    return render(request, "clientes/form.html", context)


def editar_cliente(request, id: int):
    back_url = request.GET.get("next") or reverse("clientes_lista")
    cliente = get_object_or_404(Cliente, pk=id)
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ClienteForm(instance=cliente)

    context = {"form": form, "back_url": back_url, "comisiones": _comision_pairs(form)}
    return render(request, "clientes/form.html", context)


def eliminar_cliente(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("clientes_lista")
    cliente = get_object_or_404(Cliente, pk=id)
    cliente.delete()
    return redirect(back_url)
