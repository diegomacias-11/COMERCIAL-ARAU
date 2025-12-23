from datetime import datetime, time

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import ExperienciaCliente
from .forms import ExperienciaClienteForm


def clientes_experiencia_lista(request):
    clientes = ExperienciaCliente.objects.all().order_by("-fecha_registro")

    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""
    nombre = (request.GET.get("cliente") or "").strip()

    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            clientes = clientes.filter(fecha_contrato__gte=d)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            clientes = clientes.filter(fecha_contrato__lte=d)
        except ValueError:
            pass
    if nombre:
        clientes = clientes.filter(cliente__icontains=nombre)

    return render(
        request,
        "experiencia/clientes_lista.html",
        {"clientes": clientes, "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "cliente_nombre": nombre},
    )


def editar_cliente_experiencia(request, pk):
    cliente_exp = get_object_or_404(ExperienciaCliente, pk=pk)
    back_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/experiencia/clientes/"
    contactos_url = None
    if cliente_exp.cliente_id:
        contactos_url = f"{reverse('contactos_cliente', args=[cliente_exp.cliente_id])}?next={request.get_full_path()}"
    if request.method == "POST":
        form = ExperienciaClienteForm(request.POST, instance=cliente_exp)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ExperienciaClienteForm(instance=cliente_exp)
    return render(
        request,
        "experiencia/clientes_form.html",
        {"form": form, "cliente_exp": cliente_exp, "back_url": back_url, "contactos_url": contactos_url},
    )
