from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.choices import CONTROL_PERIODICIDAD_CHOICES
from comercial.forms import ComercialKpiForm, ComercialKpiMetaForm
from comercial.models import ComercialKpi, ComercialKpiMeta, MES_CHOICES
from recursos_humanos.services.kpis.comercial import resolver_kpi


def recursos_humanos_home(request):
    return render(request, "recursos_humanos/inicio.html")


def recursos_humanos_control(request):
    areas = ["Marketing", "Comercial", "Operaciones", "Experiencia"]
    kpis_comercial = list(ComercialKpi.objects.all())
    return render(
        request,
        "recursos_humanos/control.html",
        {"areas": areas, "kpis_comercial": kpis_comercial},
    )


def recursos_humanos_comercial_control(request):
    current_year = timezone.now().year
    anio_raw = (request.GET.get("anio") or "").strip()
    periodicidad_raw = (request.GET.get("periodicidad") or "mensual").strip().lower()
    periodicidad_values = {val for val, _ in CONTROL_PERIODICIDAD_CHOICES}
    periodicidad = periodicidad_raw if periodicidad_raw in periodicidad_values else "mensual"
    try:
        anio = int(anio_raw) if anio_raw else current_year
    except ValueError:
        anio = current_year

    kpis = ComercialKpi.objects.all()
    metas = ComercialKpiMeta.objects.select_related("kpi").filter(anio=anio)
    metas_por_mes = {m: [] for m, _ in MES_CHOICES}
    for meta in metas:
        metas_por_mes.setdefault(meta.mes, []).append(meta)
    meses = [{"num": num, "nombre": label} for num, label in MES_CHOICES]

    if periodicidad == "trimestral":
        grupos = [
            ("Q1", [1, 2, 3]),
            ("Q2", [4, 5, 6]),
            ("Q3", [7, 8, 9]),
            ("Q4", [10, 11, 12]),
        ]
    elif periodicidad == "semestral":
        grupos = [("H1", [1, 2, 3, 4, 5, 6]), ("H2", [7, 8, 9, 10, 11, 12])]
    elif periodicidad == "anual":
        grupos = [("Anual", [m["num"] for m in meses])]
    else:
        grupos = [(m["nombre"], [m["num"]]) for m in meses]

    periodos = []
    for etiqueta, month_nums in grupos:
        month_blocks = []
        for num in month_nums:
            nombre = next((m["nombre"] for m in meses if m["num"] == num), "")
            month_blocks.append(
                {
                    "num": num,
                    "nombre": nombre,
                    "metas": metas_por_mes.get(num, []),
                }
            )
        periodos.append(
            {
                "label": etiqueta,
                "start": month_nums[0],
                "end": month_nums[-1],
                "months": month_blocks,
            }
        )
    context = {
        "kpis": kpis,
        "periodos": periodos,
        "anio": anio,
        "periodicidad": periodicidad,
        "periodicidad_choices": CONTROL_PERIODICIDAD_CHOICES,
    }
    return render(request, "recursos_humanos/comercial_control.html", context)


def recursos_humanos_resumen(request):
    mes_raw = (request.GET.get("mes") or "").strip()
    anio_raw = (request.GET.get("anio") or "").strip()
    start_raw = (request.GET.get("start") or "").strip()
    end_raw = (request.GET.get("end") or "").strip()
    label = (request.GET.get("label") or "").strip()
    mes = int(mes_raw) if mes_raw.isdigit() else None
    try:
        anio = int(anio_raw) if anio_raw else None
    except ValueError:
        anio = None
    start = int(start_raw) if start_raw.isdigit() else None
    end = int(end_raw) if end_raw.isdigit() else None
    mes_nombre = dict(MES_CHOICES).get(mes) if mes else ""
    periodo_titulo = ""
    if label and anio:
        periodo_titulo = f"{label} {anio}"
    elif mes_nombre and anio:
        periodo_titulo = f"{mes_nombre} {anio}"
    back_url = request.GET.get("next") or reverse("recursos_humanos_comercial_control")
    kpi_results = []
    if anio and (mes or (start and end)):
        if start and end:
            months = list(range(start, end + 1))
        else:
            months = [mes]
        metas_qs = ComercialKpiMeta.objects.filter(anio=anio, mes__in=months)
        metas = {}
        for m in metas_qs:
            metas[m.kpi_id] = metas.get(m.kpi_id, 0) + m.meta
        for kpi in ComercialKpi.objects.all():
            valor = 0
            has_kpi = False
            for m in months:
                v = resolver_kpi(kpi.nombre, m, anio)
                if v is not None:
                    has_kpi = True
                    valor += v
            if has_kpi:
                meta_val = metas.get(kpi.id)
                avance_pct = None
                avance_bar = None
                if meta_val and meta_val > 0:
                    avance_pct = (valor / float(meta_val)) * 100
                    avance_bar = max(0.0, min(100.0, avance_pct))
                kpi_results.append(
                    {
                        "nombre": kpi.nombre,
                        "meta": meta_val,
                        "valor": valor,
                        "avance_pct": avance_pct,
                        "avance_bar": avance_bar,
                    }
                )
    return render(
        request,
        "recursos_humanos/resumen.html",
        {
            "mes": mes,
            "anio": anio,
            "mes_nombre": mes_nombre,
            "periodo_titulo": periodo_titulo,
            "back_url": back_url,
            "kpi_results": kpi_results,
        },
    )


def recursos_humanos_kpi_create(request):
    back_url = request.GET.get("next") or reverse("recursos_humanos_comercial_control")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ComercialKpiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ComercialKpiForm()
    return render(request, "recursos_humanos/kpi_form.html", {"form": form, "back_url": back_url})


def recursos_humanos_kpi_update(request, pk: int):
    kpi = get_object_or_404(ComercialKpi, pk=pk)
    back_url = request.GET.get("next") or reverse("recursos_humanos_control")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ComercialKpiForm(request.POST, instance=kpi)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ComercialKpiForm(instance=kpi)
    return render(
        request,
        "recursos_humanos/kpi_form.html",
        {"form": form, "back_url": back_url, "kpi": kpi},
    )


def recursos_humanos_kpi_delete(request, pk: int):
    back_url = request.POST.get("next") or reverse("recursos_humanos_comercial_control")
    kpi = get_object_or_404(ComercialKpi, pk=pk)
    kpi.delete()
    return redirect(back_url)


def recursos_humanos_meta_create(request):
    back_url = request.GET.get("next") or reverse("recursos_humanos_comercial_control")
    initial = {}
    mes_raw = (request.GET.get("mes") or "").strip()
    anio_raw = (request.GET.get("anio") or "").strip()
    if mes_raw.isdigit():
        initial["mes"] = int(mes_raw)
    try:
        if anio_raw:
            initial["anio"] = int(anio_raw)
    except ValueError:
        pass
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ComercialKpiMetaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ComercialKpiMetaForm(
            initial=initial,
            filter_month=initial.get("mes"),
            filter_year=initial.get("anio"),
        )
    mes_nombre = dict(ComercialKpiMeta._meta.get_field("mes").choices).get(initial.get("mes"))
    return render(
        request,
        "recursos_humanos/meta_form.html",
        {
            "form": form,
            "back_url": back_url,
            "mes": initial.get("mes"),
            "anio": initial.get("anio"),
            "mes_nombre": mes_nombre,
        },
    )


def recursos_humanos_meta_update(request, pk: int):
    meta = get_object_or_404(ComercialKpiMeta, pk=pk)
    back_url = request.GET.get("next") or reverse("recursos_humanos_comercial_control")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ComercialKpiMetaForm(request.POST, instance=meta)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ComercialKpiMetaForm(
            instance=meta,
            filter_month=meta.mes,
            filter_year=meta.anio,
        )
    mes_nombre = meta.get_mes_display()
    return render(
        request,
        "recursos_humanos/meta_form.html",
        {
            "form": form,
            "back_url": back_url,
            "meta": meta,
            "mes": meta.mes,
            "anio": meta.anio,
            "mes_nombre": mes_nombre,
        },
    )


def recursos_humanos_meta_delete(request, pk: int):
    back_url = request.POST.get("next") or reverse("recursos_humanos_comercial_control")
    meta = get_object_or_404(ComercialKpiMeta, pk=pk)
    meta.delete()
    return redirect(back_url)
