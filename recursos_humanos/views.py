from django.shortcuts import render

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
    back_url = request.GET.get("next") or "/comercial/control/"
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
