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
    mes = int(mes_raw) if mes_raw.isdigit() else None
    try:
        anio = int(anio_raw) if anio_raw else None
    except ValueError:
        anio = None
    mes_nombre = dict(MES_CHOICES).get(mes) if mes else ""
    back_url = request.GET.get("next") or "/comercial/control/"
    kpi_results = []
    if mes and anio:
        metas = {
            m.kpi_id: m.meta
            for m in ComercialKpiMeta.objects.filter(mes=mes, anio=anio)
        }
        for kpi in ComercialKpi.objects.all():
            valor = resolver_kpi(kpi.nombre, mes, anio)
            if valor is not None:
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
            "back_url": back_url,
            "kpi_results": kpi_results,
        },
    )
