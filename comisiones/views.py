from datetime import date

from django.conf import settings
from django.contrib import messages
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.template.loader import render_to_string

from .forms import PagoComisionForm
from .models import Comision, PagoComision
from core.google_email import send_google_mail, GoogleEmailError


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
    comisiones_qs = Comision.objects.filter(
        periodo_mes=mes,
        periodo_anio=anio,
        pago_comision=False,
        estatus_pago_dispersion="Pagado",
    )
    if comisionista_id:
        comisiones_qs = comisiones_qs.filter(comisionista_id=comisionista_id)

    if request.method == "POST":
        form = PagoComisionForm(request.POST, comisiones_qs=comisiones_qs)
        if form.is_valid():
            pago = form.save(commit=False)
            comision = form.cleaned_data["comision"]
            pago.comision = comision
            pago.comisionista = comision.comisionista
            pago.periodo_mes = comision.periodo_mes
            pago.periodo_anio = comision.periodo_anio
            pago.monto = comision.monto
            pago.save()
            Comision.objects.filter(pk=comision.pk).update(pago_comision=True)
            return redirect(reverse("comisiones_detalle", args=[pago.comisionista_id]) + f"?mes={mes}&anio={anio}")
    else:
        form = PagoComisionForm()
        comisionista_fixed = None
        if comisionista_id:
            comisionista_fixed = comisiones_qs.select_related("comisionista").first()
        form = PagoComisionForm(comisiones_qs=comisiones_qs)
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
    comisiones_qs = Comision.objects.filter(pk=pago.comision_id)
    if request.method == "POST":
        form = PagoComisionForm(request.POST, instance=pago, comisiones_qs=comisiones_qs)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.comision = pago.comision
            obj.comisionista_id = pago.comisionista_id
            obj.periodo_mes = pago.comision.periodo_mes
            obj.periodo_anio = pago.comision.periodo_anio
            obj.monto = pago.comision.monto
            obj.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = PagoComisionForm(instance=pago, comisiones_qs=comisiones_qs)
    return render(
        request,
        "comisiones/pago_form.html",
        {"form": form, "back_url": back_url, "mes": mes, "anio": anio, "pago": pago, "comisionista": pago.comisionista},
    )


def eliminar_pago(request, id: int):
    pago = get_object_or_404(PagoComision, pk=id)
    mes, anio, _ = _coerce_mes_anio(request)
    back_url = request.POST.get("next") or f"{reverse('comisiones_detalle', args=[pago.comisionista_id])}?mes={mes}&anio={anio}"
    comision_id = pago.comision_id
    pago.delete()
    if comision_id:
        Comision.objects.filter(pk=comision_id).update(pago_comision=False)
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


def enviar_detalle_comisionista(request, comisionista_id):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir

    context = _detalle_context(comisionista_id, mes, anio)
    comisionista = context.get("comisionista")
    if not comisionista:
        messages.error(request, "No se encontraron comisiones para este comisionista.")
        return redirect(reverse("comisiones_lista") + f"?mes={mes}&anio={anio}")

    destinatario = getattr(comisionista, "correo", None)
    if not destinatario:
        messages.error(request, "El comisionista no tiene correo registrado.")
        return redirect(reverse("comisiones_detalle", args=[comisionista_id]) + f"?mes={mes}&anio={anio}")

    subject = f"Detalle de comisiones {context['mes_nombre']} {anio} - {comisionista.nombre}"
    html_body = render_to_string("comisiones/email_reporte.html", context)

    try:
        send_google_mail(
            to=destinatario,
            subject=subject,
            html_body=html_body,
            bcc=settings.EMAIL_BCC_ALWAYS or None,
        )
        messages.success(request, f"Reporte enviado a {destinatario}.")
    except GoogleEmailError as exc:
        messages.error(request, f"No se pudo enviar el correo: {exc}")
    except Exception as exc:  # pragma: no cover
        messages.error(request, f"No se pudo enviar el correo: {exc}")

    return redirect(reverse("comisiones_detalle", args=[comisionista_id]) + f"?mes={mes}&anio={anio}")
