from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, time

from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "cliente",
            "giro",
            "tipo",
            "medio",
            "contacto",
            "telefono",
            "correo",
            "conexion",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pasar fecha_registro para display en plantilla, igual que en comercial
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None) and self.instance.fecha_registro:
            self.fecha_registro_display = timezone.localtime(self.instance.fecha_registro)


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

    context = {"form": form, "back_url": back_url}
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

    context = {"form": form, "back_url": back_url}
    return render(request, "clientes/form.html", context)


def eliminar_cliente(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("clientes_lista")
    cliente = get_object_or_404(Cliente, pk=id)
    cliente.delete()
    return redirect(back_url)
