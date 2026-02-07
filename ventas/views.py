import calendar
import copy
import math
from collections import defaultdict
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from PyPDF2 import PdfReader, PdfWriter
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


def _top_with_otros(items, top_n=10):
    if not items:
        return []
    ordered = sorted(items, key=lambda x: x[1], reverse=True)
    if len(ordered) <= top_n:
        return ordered
    top = ordered[:top_n]
    otros_total = sum((val for _, val in ordered[top_n:]), Decimal("0"))
    top.append(("Otros", otros_total))
    return top


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


def _get_ventas_rango(request):
    fecha_desde_raw = request.GET.get("fecha_desde") or ""
    fecha_hasta_raw = request.GET.get("fecha_hasta") or ""
    fecha_desde = _parse_date(fecha_desde_raw)
    fecha_hasta = _parse_date(fecha_hasta_raw)

    if not fecha_desde and not fecha_hasta:
        mes_q = request.GET.get("mes")
        anio_q = request.GET.get("anio")
        mes = None
        anio = None
        try:
            mes = int(mes_q) if mes_q else None
        except Exception:
            mes = None
        try:
            anio = int(anio_q) if anio_q else None
        except Exception:
            anio = None
        if mes and anio:
            last_day = calendar.monthrange(anio, mes)[1]
            fecha_desde = date(anio, mes, 1)
            fecha_hasta = date(anio, mes, last_day)
        else:
            today = date.today()
            last_day = calendar.monthrange(today.year, today.month)[1]
            fecha_desde = date(today.year, today.month, 1)
            fecha_hasta = date(today.year, today.month, last_day)

    if fecha_desde and not fecha_hasta:
        fecha_hasta = fecha_desde
    if fecha_hasta and not fecha_desde:
        fecha_desde = fecha_hasta
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde

    return fecha_desde, fecha_hasta


def _ventas_queryset_for_rango(fecha_desde, fecha_hasta):
    ventas_qs = Venta.objects.all().select_related("cliente").order_by("fecha")
    if fecha_desde and fecha_hasta:
        ventas_qs = ventas_qs.filter(fecha__range=(fecha_desde, fecha_hasta))
    elif fecha_desde:
        ventas_qs = ventas_qs.filter(fecha__gte=fecha_desde)
    elif fecha_hasta:
        ventas_qs = ventas_qs.filter(fecha__lte=fecha_hasta)
    return ventas_qs


def _ventas_resumen_data(ventas):
    por_servicio = defaultdict(lambda: Decimal("0"))
    total_general = Decimal("0")
    total_pagado = Decimal("0")
    total_pendiente = Decimal("0")

    for venta in ventas:
        monto = venta.monto_venta or Decimal("0")
        total_general += monto
        servicio = venta.servicio or "Sin servicio"
        por_servicio[servicio] += monto
        if venta.estatus_pago == Venta.EstatusPago.PAGADO:
            total_pagado += monto
        elif venta.estatus_pago == Venta.EstatusPago.PENDIENTE:
            total_pendiente += monto

    servicios_top = _top_with_otros(list(por_servicio.items()), top_n=10)
    labels_servicio = [s for s, _ in servicios_top]
    totales_servicio = [float(v) for _, v in servicios_top]

    return {
        "labels_servicio": labels_servicio,
        "totales_servicio": totales_servicio,
        "total_general": float(total_general),
        "total_pagado": float(total_pagado),
        "total_pendiente": float(total_pendiente),
    }


def ventas_dashboard(request):
    fecha_desde, fecha_hasta = _get_ventas_rango(request)
    ventas = list(_ventas_queryset_for_rango(fecha_desde, fecha_hasta))
    resumen_data = _ventas_resumen_data(ventas)
    chart_data = {
        "labels_servicio": resumen_data["labels_servicio"],
        "totales_servicio": resumen_data["totales_servicio"],
        "total_general": resumen_data["total_general"],
        "totales_estatus": [resumen_data["total_pagado"], resumen_data["total_pendiente"]],
    }

    fecha_desde_str = fecha_desde.isoformat() if fecha_desde else ""
    fecha_hasta_str = fecha_hasta.isoformat() if fecha_hasta else ""
    fecha_desde_label = fecha_desde.strftime("%d/%m/%Y") if fecha_desde else ""
    fecha_hasta_label = fecha_hasta.strftime("%d/%m/%Y") if fecha_hasta else ""

    context = {
        "ventas_count": len(ventas),
        "fecha_desde": fecha_desde_str,
        "fecha_hasta": fecha_hasta_str,
        "fecha_desde_label": fecha_desde_label,
        "fecha_hasta_label": fecha_hasta_label,
        "chart_data": chart_data,
    }
    return render(request, "ventas/ventas_dashboard.html", context)


def _format_money(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def ventas_resumen_pdf(request):
    fecha_desde, fecha_hasta = _get_ventas_rango(request)
    ventas = list(_ventas_queryset_for_rango(fecha_desde, fecha_hasta))
    resumen_data = _ventas_resumen_data(ventas)

    desde_txt = fecha_desde.strftime("%d/%m/%Y") if fecha_desde else "—"
    hasta_txt = fecha_hasta.strftime("%d/%m/%Y") if fecha_hasta else "—"
    subtitle_text = f"Fechas: {desde_txt} a {hasta_txt}"

    template_path = settings.BASE_DIR / "static" / "img" / "MEMBRETE.pdf"
    pagesize = landscape(letter)
    if template_path.exists():
        try:
            template_reader = PdfReader(str(template_path))
            template_page = template_reader.pages[0]
            pagesize = (float(template_page.mediabox.width), float(template_page.mediabox.height))
        except Exception:
            template_reader = None
            template_page = None
    else:
        template_reader = None
        template_page = None

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        leftMargin=18,
        rightMargin=18,
        topMargin=85.04,
        bottomMargin=85.04,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = 1
    subtitle_style = styles["Heading2"]
    subtitle_style.alignment = 1
    chart_title_style = ParagraphStyle(
        "ChartTitle",
        parent=styles["Heading3"],
        alignment=1,
        textColor=colors.HexColor("#003b71"),
        fontSize=11,
        leading=12,
        spaceAfter=6,
    )

    elements = [
        Paragraph("Resumen de Ventas", title_style),
        Paragraph(subtitle_text, subtitle_style),
        Spacer(1, 10),
    ]

    page_width = pagesize[0]
    available_width = page_width - doc.leftMargin - doc.rightMargin
    chart_width = available_width
    chart_height = 200

    total_general = resumen_data["total_general"]
    if total_general <= 0 or not resumen_data["totales_servicio"]:
        labels_servicio = ["Sin ventas"]
        totales_servicio = [1]
        label_values = [0]
    else:
        labels_servicio = resumen_data["labels_servicio"]
        totales_servicio = resumen_data["totales_servicio"]
        label_values = totales_servicio

    pie = Pie()
    pie_size = min(chart_width, chart_height) * 0.9
    pie.x = (chart_width - pie_size) / 2
    pie.y = (chart_height - pie_size) / 2
    pie.width = pie_size
    pie.height = pie_size
    pie.data = totales_servicio
    pie.labels = ["" for _ in totales_servicio]
    pie.sideLabels = 0
    pie.simpleLabels = 0
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 0.5
    pie.innerRadiusFraction = 0.55

    base_blue = colors.HexColor("#59b9c7")
    for i, value in enumerate(totales_servicio):
        pct = (value / total_general) if total_general else 0
        pct = max(min(pct, 1), 0)
        r = colors.white.red + (base_blue.red - colors.white.red) * pct
        g = colors.white.green + (base_blue.green - colors.white.green) * pct
        b = colors.white.blue + (base_blue.blue - colors.white.blue) * pct
        pie.slices[i].fillColor = colors.Color(r, g, b)

    pie_drawing = Drawing(chart_width, chart_height)
    pie_drawing.add(pie)

    total_for_angles = sum(totales_servicio) or 1
    start_angle = getattr(pie, "startAngle", 90)
    angle_range = getattr(pie, "angleRange", 360) or 360
    direction = getattr(pie, "direction", "clockwise")
    center_x = pie.x + pie.width / 2
    center_y = pie.y + pie.height / 2
    outer_r = pie.width / 2
    inner_r = outer_r * (pie.innerRadiusFraction or 0)
    label_r = inner_r + (outer_r - inner_r) * 0.55
    line_gap = 10
    single_slice = len(totales_servicio) == 1
    for label, value in zip(labels_servicio, label_values):
        angle = (value / total_for_angles) * angle_range
        if angle <= 0:
            continue
        if single_slice:
            x = center_x
            y = center_y
        else:
            mid = start_angle - (angle / 2) if direction == "clockwise" else start_angle + (angle / 2)
            theta = math.radians(mid)
            x = center_x + label_r * math.cos(theta)
            y = center_y + label_r * math.sin(theta)
        pct = (value / total_general * 100) if total_general else 0
        t1 = String(x, y + (line_gap / 2), f"{label}")
        t1.fontName = "Helvetica-Bold"
        t1.fontSize = 8
        t1.fillColor = colors.HexColor("#003b71")
        t1.textAnchor = "middle"
        t2 = String(x, y - (line_gap / 2), f"{_format_money(value)} ({pct:.1f}%)")
        t2.fontName = "Helvetica"
        t2.fontSize = 8
        t2.fillColor = colors.HexColor("#003b71")
        t2.textAnchor = "middle"
        pie_drawing.add(t1)
        pie_drawing.add(t2)
        start_angle = start_angle - angle if direction == "clockwise" else start_angle + angle

    bar = VerticalBarChart()
    bar.x = 32
    bar.y = 20
    bar.width = chart_width - 50
    bar.height = chart_height - 40
    bar.data = [[resumen_data["total_pagado"], resumen_data["total_pendiente"]]]
    bar.categoryAxis.categoryNames = ["Pagado", "Pendiente"]
    bar.categoryAxis.labels.boxAnchor = "n"
    bar.categoryAxis.labels.dy = -2
    bar.categoryAxis.labels.fontName = "Helvetica-Bold"
    bar.categoryAxis.labels.fontSize = 9
    bar.categoryAxis.labels.fillColor = colors.HexColor("#003b71")
    bar.valueAxis.labelTextFormat = lambda v: _format_money(v)
    bar.valueAxis.labels.fontSize = 7
    bar.valueAxis.labels.fillColor = colors.HexColor("#003b71")
    bar.valueAxis.valueMin = 0
    max_val = max(resumen_data["total_pagado"], resumen_data["total_pendiente"], 1)
    bar.valueAxis.valueMax = max_val * 1.2
    bar.valueAxis.valueStep = max_val / 4 if max_val > 0 else 1
    bar.barWidth = 28
    bar.barSpacing = 12
    bar.groupSpacing = 18
    bar.barLabels.nudge = 6
    bar.barLabels.fontName = "Helvetica-Bold"
    bar.barLabels.fontSize = 8
    bar.barLabels.fillColor = colors.HexColor("#003b71")
    bar.barLabelFormat = lambda v: _format_money(v)
    bar.bars[(0, 0)].fillColor = colors.HexColor("#0a7a4d")
    bar.bars[(0, 1)].fillColor = colors.HexColor("#f3b0b0")

    bar_drawing = Drawing(chart_width, chart_height)
    bar_drawing.add(bar)

    charts_table = Table(
        [
            [[Paragraph("Ventas por servicio", chart_title_style), pie_drawing]],
            [[Paragraph("Total pagado vs pendiente", chart_title_style), bar_drawing]],
        ],
        colWidths=[chart_width],
    )
    charts_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(charts_table)

    doc.build(elements)
    content_pdf = buffer.getvalue()
    buffer.close()

    if template_reader and template_page:
        content_reader = PdfReader(BytesIO(content_pdf))
        writer = PdfWriter()
        for page in content_reader.pages:
            base = copy.copy(template_page)
            if base.mediabox != page.mediabox:
                base.mediabox = page.mediabox
            base.merge_page(page)
            writer.add_page(base)
        output = BytesIO()
        writer.write(output)
        pdf = output.getvalue()
        output.close()
    else:
        pdf = content_pdf

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="resumen_ventas.pdf"'
    return response


def agregar_venta(request):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir and request.method != "POST":
        return redir
    back_url = request.GET.get("next") or f"{reverse('ventas_venta_list')}?mes={mes}&anio={anio}"

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
    back_url = request.GET.get("next") or f"{reverse('ventas_venta_list')}?mes={mes}&anio={anio}"
    if request.method == "POST":
        form = VentaForm(request.POST, instance=venta, mes=mes, anio=anio)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = VentaForm(instance=venta, mes=mes, anio=anio)
    return render(request, "ventas/venta_form.html", {"form": form, "venta": venta, "back_url": back_url, "mes": mes, "anio": anio})


def eliminar_venta(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("ventas_venta_list")
    venta = get_object_or_404(Venta, pk=id)
    venta.delete()
    return redirect(back_url)
