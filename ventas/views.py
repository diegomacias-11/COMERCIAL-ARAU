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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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


def _get_ventas_rango(request, allow_empty=False):
    fecha_desde_raw = request.GET.get("fecha_desde") or ""
    fecha_hasta_raw = request.GET.get("fecha_hasta") or ""
    fecha_desde = _parse_date(fecha_desde_raw)
    fecha_hasta = _parse_date(fecha_hasta_raw)

    if not fecha_desde and not fecha_hasta:
        if allow_empty:
            return None, None
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
    fecha_desde, fecha_hasta = _get_ventas_rango(request, allow_empty=True)
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
        "total_ventas_display": _format_money(resumen_data["total_general"]),
    }
    return render(request, "ventas/ventas_dashboard.html", context)


def _format_money(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def _format_fecha_larga(value):
    if not value:
        return "—"
    meses = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    return f"{value.day:02d} de {meses[value.month - 1]} del {value.year}"


def _try_register_poppins():
    font_dir = settings.BASE_DIR / "static" / "fonts"
    if not font_dir.exists():
        return None, None

    def pick(names):
        for name in names:
            path = font_dir / name
            if path.exists():
                return path
        return None

    regular_path = pick(["Poppins-Regular.ttf", "Poppins.ttf"])
    bold_path = pick(["Poppins-Bold.ttf", "Poppins-SemiBold.ttf"])
    italic_path = pick(["Poppins-Italic.ttf"])
    bold_italic_path = pick(["Poppins-BoldItalic.ttf", "Poppins-Italic.ttf"])

    try:
        if regular_path:
            pdfmetrics.registerFont(TTFont("Poppins", str(regular_path)))
        if bold_path:
            pdfmetrics.registerFont(TTFont("Poppins-Bold", str(bold_path)))
        if italic_path:
            pdfmetrics.registerFont(TTFont("Poppins-Italic", str(italic_path)))
        if bold_italic_path:
            pdfmetrics.registerFont(TTFont("Poppins-BoldItalic", str(bold_italic_path)))
        if regular_path and bold_path:
            pdfmetrics.registerFontFamily(
                "Poppins",
                normal="Poppins",
                bold="Poppins-Bold",
                italic="Poppins-Italic" if italic_path else "Poppins",
                boldItalic="Poppins-BoldItalic" if bold_italic_path else "Poppins-Bold",
            )
        return ("Poppins" if regular_path else None, "Poppins-Bold" if bold_path else None)
    except Exception:
        return None, None


def ventas_resumen_pdf(request):
    fecha_desde, fecha_hasta = _get_ventas_rango(request, allow_empty=True)
    ventas = list(_ventas_queryset_for_rango(fecha_desde, fecha_hasta))
    resumen_data = _ventas_resumen_data(ventas)

    if not fecha_desde and not fecha_hasta:
        fechas = [v.fecha for v in ventas if v.fecha]
        if fechas:
            fecha_desde = min(fechas)
            fecha_hasta = max(fechas)

    desde_txt = _format_fecha_larga(fecha_desde)
    hasta_txt = _format_fecha_larga(fecha_hasta)
    subtitle_text = f"Fechas:<br/>{desde_txt}<br/>{hasta_txt}"

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
    poppins_regular, poppins_bold = _try_register_poppins()
    font_regular = poppins_regular or "Helvetica"
    font_bold = poppins_bold or "Helvetica-Bold"
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = 1
    title_style.textColor = colors.HexColor("#003b71")
    title_style.fontName = font_bold
    subtitle_style = styles["Heading2"]
    subtitle_style.alignment = 2
    subtitle_style.textColor = colors.HexColor("#003b71")
    subtitle_style.fontName = font_regular
    subtitle_style.fontSize = 10
    subtitle_style.leading = 12
    chart_title_style = ParagraphStyle(
        "ChartTitle",
        parent=styles["Heading3"],
        alignment=1,
        textColor=colors.HexColor("#003b71"),
        fontSize=11,
        leading=12,
        spaceAfter=6,
        fontName=font_bold,
    )

    page_width = pagesize[0]
    available_width = page_width - doc.leftMargin - doc.rightMargin
    total_general = resumen_data["total_general"]

    total_box = Table(
        [[f"Total ventas: {_format_money(total_general)}"]],
        colWidths=[available_width * 0.32],
    )
    total_box.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef3f7")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#003b71")),
                ("FONTNAME", (0, 0), (-1, -1), font_bold),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("INNERPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#aebed2")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    top_bar = Table([[""]], colWidths=[available_width], rowHeights=[16])
    top_bar.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#59b9c7")),
                ("INNERPADDING", (0, 0), (-1, -1), 0),
                ("BOX", (0, 0), (-1, -1), 0, colors.white),
            ]
        )
    )

    right_stack = Table(
        [
            [Paragraph(subtitle_text, subtitle_style)],
            [total_box],
        ],
        colWidths=[available_width * 0.35],
    )
    right_stack.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    header_table = Table(
        [
            [
                Paragraph("Resumen de Ventas", title_style),
                right_stack,
            ]
        ],
        colWidths=[available_width * 0.65, available_width * 0.35],
        rowHeights=[38],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    header_separator = Table([[""]], colWidths=[available_width])
    header_separator.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor("#aebed2")),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    header_spacer = Table([[""]], colWidths=[available_width], rowHeights=[6])

    elements = [
        top_bar,
        Spacer(1, 12),
        header_table,
        header_spacer,
        header_separator,
        Spacer(1, 10),
    ]

    chart_width = available_width
    chart_height = 200
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
    dark_blue = colors.HexColor("#003b71")
    slice_colors = []
    for i, value in enumerate(totales_servicio):
        pct = (value / total_general) if total_general else 0
        pct = max(min(pct, 1), 0)
        t = 0.25 + (0.75 * pct)
        r = base_blue.red + (dark_blue.red - base_blue.red) * t
        g = base_blue.green + (dark_blue.green - base_blue.green) * t
        b = base_blue.blue + (dark_blue.blue - base_blue.blue) * t
        color = colors.Color(r, g, b)
        pie.slices[i].fillColor = color
        slice_colors.append(color)

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
    for idx, (label, value) in enumerate(zip(labels_servicio, label_values)):
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
        slice_color = slice_colors[idx] if idx < len(slice_colors) else colors.HexColor("#59b9c7")
        lum = (
            0.2126 * slice_color.red
            + 0.7152 * slice_color.green
            + 0.0722 * slice_color.blue
        )
        label_fill = colors.white if lum < 0.55 else colors.HexColor("#003b71")

        t1 = String(x, y + (line_gap / 2), f"{label}")
        t1.fontName = font_bold
        t1.fontSize = 8
        t1.fillColor = label_fill
        t1.textAnchor = "middle"
        t2 = String(x, y - (line_gap / 2), f"{_format_money(value)} ({pct:.1f}%)")
        t2.fontName = font_regular
        t2.fontSize = 8
        t2.fillColor = label_fill
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
    bar.categoryAxis.labels.fontName = font_bold
    bar.categoryAxis.labels.fontSize = 9
    bar.categoryAxis.labels.fillColor = colors.HexColor("#003b71")
    bar.valueAxis.labels.fontName = font_regular
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
    bar.strokeColor = colors.transparent
    bar.barLabels.nudge = 6
    bar.barLabels.fontName = font_bold
    bar.barLabels.fontSize = 8
    bar.barLabels.fillColor = colors.HexColor("#003b71")
    bar.barLabelFormat = lambda v: _format_money(v)
    bar.bars[(0, 0)].fillColor = colors.HexColor("#0a7a4d")
    bar.bars[(0, 1)].fillColor = colors.HexColor("#f3b0b0")
    bar.bars[(0, 0)].strokeColor = colors.transparent
    bar.bars[(0, 1)].strokeColor = colors.transparent

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
