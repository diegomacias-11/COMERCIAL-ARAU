from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect

from .forms import _cliente_choices, ActividadMercaForm
from .models import ActividadMerca


ESTATUS_CHOICES = [
    "En tiempo",
    "Vence hoy",
    "Se entregó tarde",
    "Entregada a tiempo",
]


def _parse_date(val: str | None):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        return None


def actividades_lista(request):
    qs = ActividadMerca.objects.all().order_by("-fecha_inicio")

    f_desde = _parse_date(request.GET.get("fecha_inicio"))
    f_hasta = _parse_date(request.GET.get("fecha_fin"))
    cliente_sel = request.GET.get("cliente") or ""
    estatus_sel = request.GET.get("estatus") or ""

    if f_desde:
        qs = qs.filter(fecha_inicio__gte=f_desde)
    if f_hasta:
        qs = qs.filter(fecha_inicio__lte=f_hasta)
    if cliente_sel:
        qs = qs.filter(cliente__iexact=cliente_sel)

    actividades = list(qs)
    if estatus_sel:
        actividades = [a for a in actividades if a.estatus == estatus_sel]

    context = {
        "actividades": actividades,
        "clientes_choices": _cliente_choices(),
        "estatus_choices": ESTATUS_CHOICES,
        "f_desde": request.GET.get("fecha_inicio", ""),
        "f_hasta": request.GET.get("fecha_fin", ""),
        "cliente_sel": cliente_sel,
        "estatus_sel": estatus_sel,
    }
    return render(request, "actividades_merca/lista.html", context)


def crear_actividad(request):
    back_url = request.GET.get("next") or "/actividades_merca/"
    if request.method == "POST":
        form = ActividadMercaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ActividadMercaForm(user=request.user)
    return render(
        request,
        "actividades_merca/form.html",
        {
            "form": form,
            "back_url": back_url,
        },
    )


def editar_actividad(request, pk: int):
    actividad = get_object_or_404(ActividadMerca, pk=pk)
    back_url = request.GET.get("next") or "/actividades_merca/"
    if request.method == "POST":
        form = ActividadMercaForm(request.POST, instance=actividad, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ActividadMercaForm(instance=actividad, user=request.user)
    return render(
        request,
        "actividades_merca/form.html",
        {
            "form": form,
            "back_url": back_url,
            "actividad": actividad,
        },
    )


def eliminar_actividad(request, pk: int):
    back_url = request.POST.get("next") or request.GET.get("next") or "/actividades_merca/"
    actividad = get_object_or_404(ActividadMerca, pk=pk)
    actividad.delete()
    return redirect(back_url)
