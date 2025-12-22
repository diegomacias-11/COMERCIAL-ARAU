from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import VentaForm
from .models import Venta


def _coerce_mes_anio(request):
    today = date.today()
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    if not mes or not anio:
        return None, None, redirect(f"{request.path}?mes={today.month}&anio={today.year}")
    try:
        mes_i = int(mes)
        if mes_i < 1 or mes_i > 12:
            mes_i = today.month
    except Exception:
        mes_i = today.month
    try:
        anio_i = int(anio)
    except Exception:
        anio_i = today.year
    return mes_i, anio_i, None


def ventas_lista(request):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir

    estatus_pago = request.GET.get("estatus_pago") or ""

    ventas = Venta.objects.filter(fecha__month=mes, fecha__year=anio)
    if estatus_pago:
        ventas = ventas.filter(estatus_pago=estatus_pago)
    ventas = ventas.order_by("fecha")
    meses_nombres = [
        "",
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    meses_choices = [(i, meses_nombres[i]) for i in range(1, 13)]
    context = {
        "ventas": ventas,
        "mes": str(mes),
        "anio": str(anio),
        "meses": list(range(1, 13)),
        "meses_choices": meses_choices,
        "mes_nombre": meses_nombres[mes],
        "estatus_pago": estatus_pago,
        "estatus_pago_choices": Venta.EstatusPago.choices,
    }
    return render(request, "ventas/ventas_lista.html", context)


def agregar_venta(request):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir and request.method != "POST":
        return redir
    back_url = request.GET.get("next") or f"{reverse('ventas_lista')}?mes={mes}&anio={anio}"

    if request.method == "POST":
        mes = int(request.POST.get("mes") or mes or datetime.now().month)
        anio = int(request.POST.get("anio") or anio or datetime.now().year)
        form = VentaForm(request.POST, mes=mes, anio=anio)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = VentaForm(mes=mes, anio=anio)
    return render(request, "ventas/venta_form.html", {"form": form, "back_url": back_url, "mes": mes, "anio": anio})


def editar_venta(request, id: int):
    venta = get_object_or_404(Venta, pk=id)
    mes, anio, _ = _coerce_mes_anio(request)
    back_url = request.GET.get("next") or f"{reverse('ventas_lista')}?mes={mes}&anio={anio}"
    if request.method == "POST":
        form = VentaForm(request.POST, instance=venta, mes=mes, anio=anio)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = VentaForm(instance=venta, mes=mes, anio=anio)
    return render(request, "ventas/venta_form.html", {"form": form, "venta": venta, "back_url": back_url, "mes": mes, "anio": anio})


def eliminar_venta(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("ventas_lista")
    venta = get_object_or_404(Venta, pk=id)
    venta.delete()
    return redirect(back_url)
