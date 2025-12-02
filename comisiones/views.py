from datetime import date

from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import PagoComisionForm
from .models import Comision, PagoComision


MESES_NOMBRES = [
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


def comisiones_lista(request):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir

    Comision.objects.filter(periodo_mes=mes, periodo_anio=anio, venta__estatus_pago="Pagado").update(
        liberada=True, estatus_pago_dispersion="Pagado"
    )
    Comision.objects.filter(periodo_mes=mes, periodo_anio=anio).exclude(venta__estatus_pago="Pagado").update(
        liberada=False
    )

    qs_periodo = Comision.objects.filter(periodo_mes=mes, periodo_anio=anio)
    resumen = list(
        qs_periodo.values("comisionista_id", "comisionista__nombre")
        .annotate(total=Sum("monto"), liberadas=Sum("monto", filter=Q(liberada=True)))
        .order_by("comisionista__nombre")
    )

    pagos = PagoComision.objects.filter(periodo_mes=mes, periodo_anio=anio).values("comisionista_id").annotate(
        pagos=Sum("monto")
    )
    pagos_map = {p["comisionista_id"]: p["pagos"] for p in pagos}
    for r in resumen:
        r["pagos"] = pagos_map.get(r["comisionista_id"], 0) or 0
        r["pendiente"] = (r["liberadas"] or 0) - (r["pagos"] or 0)

    total_periodo = qs_periodo.aggregate(v=Sum("monto"))["v"] or 0
    total_liberado = qs_periodo.filter(liberada=True).aggregate(v=Sum("monto"))["v"] or 0
    total_pagos = PagoComision.objects.filter(periodo_mes=mes, periodo_anio=anio).aggregate(v=Sum("monto"))["v"] or 0
    total_pendiente = total_liberado - total_pagos

    meses_choices = [(i, MESES_NOMBRES[i]) for i in range(1, 13)]
    context = {
        "mes": str(mes),
        "anio": str(anio),
        "resumen": resumen,
        "meses": list(range(1, 13)),
        "meses_choices": meses_choices,
        "mes_nombre": MESES_NOMBRES[mes],
        "total_periodo": total_periodo,
        "total_liberado": total_liberado,
        "total_pagos": total_pagos,
        "total_pendiente": total_pendiente,
    }
    return render(request, "comisiones/comisiones_lista.html", context)


def comisiones_detalle(request, comisionista_id):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir
    context = _detalle_context(comisionista_id, mes, anio)
    return render(request, "comisiones/comisiones_detalle.html", context)


def registrar_pago(request, comisionista_id: int = None):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir and request.method != "POST":
        return redir
    back_url = f"{reverse('comisiones_lista')}?mes={mes}&anio={anio}"

    from alianzas.models import Alianza

    com_ids = (
        Comision.objects.filter(periodo_mes=mes, periodo_anio=anio)
        .values_list("comisionista_id", flat=True)
        .distinct()
    )
    qset = Alianza.objects.filter(id__in=list(com_ids))

    if request.method == "POST":
        form = PagoComisionForm(request.POST)
        form.fields["comisionista"].queryset = qset
        if form.is_valid():
            pago = form.save(commit=False)
            if comisionista_id:
                pago.comisionista_id = comisionista_id
            else:
                pago.comisionista = form.cleaned_data["comisionista"]
            pago.periodo_mes = mes
            pago.periodo_anio = anio
            pago.save()
            return redirect(reverse("comisiones_detalle", args=[pago.comisionista_id]) + f"?mes={mes}&anio={anio}")
    else:
        form = PagoComisionForm()
        form.fields["comisionista"].queryset = qset
        comisionista_fixed = None
        if comisionista_id:
            form.fields["comisionista"].initial = comisionista_id
            form.fields["comisionista"].disabled = True
            comisionista_fixed = qset.filter(id=comisionista_id).first()
    return render(
        request,
        "comisiones/pago_form.html",
        {
            "form": form,
            "back_url": back_url,
            "mes": mes,
            "anio": anio,
            "comisionista": comisionista_fixed if comisionista_id else None,
            "mes_nombre": MESES_NOMBRES[mes],
        },
    )


def editar_pago(request, id: int):
    pago = get_object_or_404(PagoComision, pk=id)
    mes, anio, _ = _coerce_mes_anio(request)
    back_url = f"{reverse('comisiones_detalle', args=[pago.comisionista_id])}?mes={mes}&anio={anio}"

    from alianzas.models import Alianza

    com_ids = (
        Comision.objects.filter(periodo_mes=mes, periodo_anio=anio)
        .values_list("comisionista_id", flat=True)
        .distinct()
    )
    qset = Alianza.objects.filter(id__in=list(com_ids))
    if request.method == "POST":
        form = PagoComisionForm(request.POST, instance=pago)
        form.fields["comisionista"].queryset = qset
        form.fields["comisionista"].disabled = True
        if form.is_valid():
            obj = form.save(commit=False)
            obj.comisionista_id = pago.comisionista_id
            obj.periodo_mes = mes
            obj.periodo_anio = anio
            obj.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = PagoComisionForm(instance=pago)
        form.fields["comisionista"].queryset = qset
        form.fields["comisionista"].initial = pago.comisionista_id
        form.fields["comisionista"].disabled = True
    return render(
        request,
        "comisiones/pago_form.html",
        {"form": form, "back_url": back_url, "mes": mes, "anio": anio, "pago": pago, "comisionista": pago.comisionista},
    )


def eliminar_pago(request, id: int):
    pago = get_object_or_404(PagoComision, pk=id)
    mes, anio, _ = _coerce_mes_anio(request)
    back_url = request.POST.get("next") or f"{reverse('comisiones_detalle', args=[pago.comisionista_id])}?mes={mes}&anio={anio}"
    pago.delete()
    return redirect(back_url)


def _detalle_context(comisionista_id, mes, anio):
    qs = Comision.objects.filter(periodo_mes=mes, periodo_anio=anio, comisionista_id=comisionista_id).select_related(
        "venta", "cliente", "comisionista"
    )
    pagos = PagoComision.objects.filter(periodo_mes=mes, periodo_anio=anio, comisionista_id=comisionista_id).order_by(
        "fecha_pago"
    )
    total_periodo = qs.aggregate(v=Sum("monto"))["v"] or 0
    total_liberado = qs.filter(liberada=True).aggregate(v=Sum("monto"))["v"] or 0
    total_pagos = pagos.aggregate(v=Sum("monto"))["v"] or 0
    total_pendiente = total_liberado - total_pagos
    return {
        "mes": str(mes),
        "anio": str(anio),
        "comisionista": qs.first().comisionista if qs.exists() else None,
        "items": qs,
        "meses": list(range(1, 13)),
        "mes_nombre": MESES_NOMBRES[mes],
        "pagos": pagos,
        "total_periodo": total_periodo,
        "total_liberado": total_liberado,
        "total_pagos": total_pagos,
        "total_pendiente": total_pendiente,
    }
