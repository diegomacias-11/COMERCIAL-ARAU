from datetime import datetime
from io import BytesIO
import copy

from django import forms
from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from PyPDF2 import PdfReader, PdfWriter

from .models import GastoMercadotecnia

class GastoMercadotecniaForm(forms.ModelForm):
    class Meta:
        model = GastoMercadotecnia
        fields = [
            "fecha_facturacion",
            "categoria",
            "plataforma",
            "marca",
            "tdc",
            "tipo_facturacion",
            "periodicidad",
            "facturacion",
            "notas",
        ]
        widgets = {
            "fecha_facturacion": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("categoria", "plataforma", "marca", "tdc", "tipo_facturacion", "periodicidad"):
            if name in self.fields:
                choices = list(self.fields[name].choices)
                self.fields[name].choices = [("", "----")] + choices
        if self.instance and getattr(self.instance, "pk", None) and self.instance.fecha_facturacion:
            try:
                self.initial["fecha_facturacion"] = self.instance.fecha_facturacion.isoformat()
            except Exception:
                pass


def gastos_lista(request):
    gastos = GastoMercadotecnia.objects.all().order_by("-fecha_facturacion", "-creado")
    fecha_desde = (request.GET.get("fecha_desde") or "").strip()
    fecha_hasta = (request.GET.get("fecha_hasta") or "").strip()
    marca = (request.GET.get("marca") or "").strip()

    if fecha_desde:
        gastos = gastos.filter(fecha_facturacion__gte=fecha_desde)
    if fecha_hasta:
        gastos = gastos.filter(fecha_facturacion__lte=fecha_hasta)
    if marca:
        gastos = gastos.filter(marca=marca)
    total_facturacion = gastos.aggregate(total=Sum("facturacion"))["total"] or 0

    context = {
        "gastos": gastos,
        "total_facturacion": total_facturacion,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "marca": marca,
        "marca_choices": GastoMercadotecnia._meta.get_field("marca").choices,
    }
    return render(request, "gastos_mercadotecnia/lista.html", context)


def _parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def reporte_gastos(request):
    fecha_desde = _parse_date(request.GET.get("fecha_desde") or "")
    fecha_hasta = _parse_date(request.GET.get("fecha_hasta") or "")
    marca = (request.GET.get("marca") or "").strip()

    qs = GastoMercadotecnia.objects.all().order_by("-fecha_facturacion", "-creado")
    if fecha_desde:
        qs = qs.filter(fecha_facturacion__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_facturacion__lte=fecha_hasta)
    if marca:
        qs = qs.filter(marca=marca)

    marca_txt = marca or "Todas"
    title_text = f"Reporte de inversiones - Marca: {marca_txt}"
    if fecha_desde or fecha_hasta:
        desde_txt = fecha_desde.strftime("%d/%m/%Y") if fecha_desde else ""
        hasta_txt = fecha_hasta.strftime("%d/%m/%Y") if fecha_hasta else ""
        subtitle_text = f"Fechas: {desde_txt} a {hasta_txt}"
    else:
        subtitle_text = "Fechas: "

    total_facturacion = sum([g.facturacion or 0 for g in qs])
    total_text = f"Total facturación: ${total_facturacion:,.2f}"

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
    body_style = styles["BodyText"]
    body_style.fontSize = 8
    body_style.leading = 10

    elements = [
        Paragraph(title_text, title_style),
        Paragraph(subtitle_text, subtitle_style),
        Spacer(1, 6),
    ]

    total_table = Table([[total_text]])
    total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0.88, 0.93, 0.98)),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f4c75")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#aebed2")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.extend([total_table, Spacer(1, 12)])

    header_style = styles["BodyText"]
    header_style.fontSize = 8
    header_style.leading = 10
    table_data = [
        [
            Paragraph("Fecha facturación", header_style),
            Paragraph("Categoría", header_style),
            Paragraph("Plataforma", header_style),
            Paragraph("Marca", header_style),
            Paragraph("TDC", header_style),
            Paragraph("Tipo facturación", header_style),
            Paragraph("Periodicidad<br/>", header_style),
            Paragraph("Facturación<br/>", header_style),
            Paragraph("Notas", header_style),
        ]
    ]
    for g in qs:
        table_data.append(
            [
                g.fecha_facturacion.strftime("%d/%m/%Y") if g.fecha_facturacion else "",
                Paragraph(g.categoria or "", body_style),
                Paragraph(g.plataforma or "", body_style),
                Paragraph(g.marca or "", body_style),
                Paragraph(g.tdc or "", body_style),
                Paragraph(g.tipo_facturacion or "", body_style),
                Paragraph(g.periodicidad or "", body_style),
                f"${(g.facturacion or 0):,.2f}",
                Paragraph(g.notas or "", body_style),
            ]
        )

    page_width = pagesize[0]
    available_width = page_width - doc.leftMargin - doc.rightMargin
    col_widths = [
        available_width * 0.115,  # Fecha facturación
        available_width * 0.105,  # Categoría
        available_width * 0.105,  # Plataforma
        available_width * 0.075,  # Marca
        available_width * 0.065,  # TDC
        available_width * 0.105,  # Tipo facturación
        available_width * 0.11,   # Periodicidad
        available_width * 0.105,  # Facturación
        available_width * 0.215,  # Notas
    ]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    header_bg = colors.Color(0.90, 0.93, 0.96, alpha=0.3)
    row_bg = colors.Color(0.97, 0.98, 0.99, alpha=0.3)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2a3d")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#aebed2")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("WORDWRAP", (0, 0), (-1, -1), True),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.Color(1, 1, 1, alpha=0.0), row_bg]),
            ]
        )
    )
    elements.append(table)
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
    response["Content-Disposition"] = 'inline; filename="reporte_inversiones.pdf"'
    return response


def gastos_crear(request):
    back_url = request.GET.get("next") or reverse("gastos_mercadotecnia_gasto_list")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = GastoMercadotecniaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = GastoMercadotecniaForm()
    return render(request, "gastos_mercadotecnia/form.html", {"form": form, "back_url": back_url})


def gastos_editar(request, pk: int):
    gasto = get_object_or_404(GastoMercadotecnia, pk=pk)
    back_url = request.GET.get("next") or reverse("gastos_mercadotecnia_gasto_list")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = GastoMercadotecniaForm(request.POST, instance=gasto)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = GastoMercadotecniaForm(instance=gasto)
    return render(request, "gastos_mercadotecnia/form.html", {"form": form, "back_url": back_url, "gasto": gasto})
