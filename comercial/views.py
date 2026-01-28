from datetime import datetime, time
from io import BytesIO

from django import forms
from django.db.models import Max, Min
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from PyPDF2 import PdfReader, PdfWriter
import copy
from django.conf import settings
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.choices import CONTROL_PERIODICIDAD_CHOICES, SERVICIO_CHOICES
from .forms import ComercialKpiForm, ComercialKpiMetaForm
from .models import Cita, ComercialKpi, ComercialKpiMeta, MES_CHOICES, NUM_CITA_CHOICES


class CitaForm(forms.ModelForm):
    fecha_cita = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
        required=True,
        label="Fecha de la cita",
    )

    def __init__(self, *args, **kwargs):
        from django.utils import timezone

        super().__init__(*args, **kwargs)
        # Al editar, mostrar la fecha en formato compatible con datetime-local
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None) and self.instance.fecha_cita:
            local_dt = timezone.localtime(self.instance.fecha_cita)
            self.initial["fecha_cita"] = local_dt.strftime("%Y-%m-%dT%H:%M")
        # Pasar fecha_registro para display
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None) and self.instance.fecha_registro:
            self.fecha_registro_display = timezone.localtime(self.instance.fecha_registro)

    class Meta:
        model = Cita
        fields = [
            "prospecto",
            "giro",
            "tipo",
            "servicio",
            "servicio2",
            "servicio3",
            "contacto",
            "puesto",
            "telefono",
            "correo",
            "conexion",
            "domicilio",
            "pagina_web",
            "linkedin",
            "otra_red",
            "propuesta",
            "medio",
            "estatus_cita",
            "fecha_cita",
            "numero_cita",
            "lugar",
            "estatus_seguimiento",
            "comentarios",
            "vendedor",
        ]
        widgets = {}


NUMERO_CITA_ORDER = [choice for choice, _ in NUM_CITA_CHOICES]


def _siguiente_numero_cita(actual):
    """
    Devuelve el valor siguiente de numero_cita respetando el orden de NUM_CITA_CHOICES.
    Si no hay siguiente o no coincide con la lista, se regresa el valor original.
    """
    if actual in NUMERO_CITA_ORDER:
        idx = NUMERO_CITA_ORDER.index(actual)
        if idx + 1 < len(NUMERO_CITA_ORDER):
            return NUMERO_CITA_ORDER[idx + 1]
    return actual


def _initial_desde_cita(cita: Cita) -> dict:
    """Construye los valores iniciales para registrar una nueva cita tomando otra como base."""
    return {
        "prospecto": cita.prospecto,
        "giro": cita.giro,
        "tipo": cita.tipo,
        "servicio": cita.servicio,
        "servicio2": cita.servicio2,
        "servicio3": cita.servicio3,
        "contacto": cita.contacto,
        "puesto": cita.puesto,
        "telefono": cita.telefono,
        "correo": cita.correo,
        "conexion": cita.conexion,
        "domicilio": cita.domicilio,
        "pagina_web": cita.pagina_web,
        "linkedin": cita.linkedin,
        "otra_red": cita.otra_red,
        "propuesta": cita.propuesta,
        "medio": cita.medio,
        "estatus_cita": cita.estatus_cita,
        "numero_cita": _siguiente_numero_cita(cita.numero_cita),
        "lugar": cita.lugar,
        "estatus_seguimiento": cita.estatus_seguimiento,
        "comentarios": cita.comentarios,
        "vendedor": cita.vendedor,
        # fecha_cita se deja en blanco para obligar a definir la nueva
    }


def citas_lista(request):
    citas = Cita.objects.all().order_by("-fecha_registro")
    fecha_desde = (request.GET.get("fecha_desde") or "").strip()
    fecha_hasta = (request.GET.get("fecha_hasta") or "").strip()
    prospecto = (request.GET.get("prospecto") or "").strip()
    servicio = (request.GET.get("servicio") or "").strip()
    estatus_cita = (request.GET.get("estatus_cita") or "").strip()
    estatus_seguimiento = (request.GET.get("estatus_seguimiento") or "").strip()

    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(d, time.min), tz)
            citas = citas.filter(fecha_cita__gte=start_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(d, time.max), tz)
            citas = citas.filter(fecha_cita__lte=end_dt)
        except ValueError:
            pass
    if prospecto:
        citas = citas.filter(prospecto__icontains=prospecto)
    if servicio:
        citas = citas.filter(servicio=servicio)
    if estatus_cita:
        citas = citas.filter(estatus_cita=estatus_cita)
    if estatus_seguimiento:
        citas = citas.filter(estatus_seguimiento=estatus_seguimiento)
    context = {
        "citas": citas,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "prospecto": prospecto,
        "servicio": servicio,
        "estatus_cita": estatus_cita,
        "estatus_seguimiento": estatus_seguimiento,
        "servicio_choices": SERVICIO_CHOICES,
        "estatus_cita_choices": Cita._meta.get_field("estatus_cita").choices,
        "estatus_seguimiento_choices": Cita._meta.get_field("estatus_seguimiento").choices,
    }
    return render(request, "comercial/lista.html", context)


def _filter_citas_queryset(request):
    citas = Cita.objects.all().order_by("-fecha_registro")
    fecha_desde = (request.GET.get("fecha_desde") or "").strip()
    fecha_hasta = (request.GET.get("fecha_hasta") or "").strip()

    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(d, time.min), tz)
            citas = citas.filter(fecha_cita__gte=start_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(d, time.max), tz)
            citas = citas.filter(fecha_cita__lte=end_dt)
        except ValueError:
            pass
    return citas, fecha_desde, fecha_hasta


def _build_citas_kanban_data(citas):
    total_citas = citas.count()
    total_atendidas = citas.filter(estatus_cita="Atendida").count()
    total_cerradas = citas.filter(estatus_seguimiento="Cerrado").count()

    seguimiento_order = [val for val, _ in Cita._meta.get_field("estatus_seguimiento").choices]
    seguimiento_order.append("Sin seguimiento")

    columnas = [
        {"key": "Cancelada", "title": "Canceladas", "statuses": ["Cancelada"], "class": "status-cancelada"},
        {"key": "Agendada", "title": "Agendadas", "statuses": ["Agendada", "Pospuesta"], "class": "status-agendada"},
        {"key": "Atendida", "title": "Atendidas", "statuses": ["Atendida"], "class": "status-atendida"},
    ]

    kanban_data = []
    for col in columnas:
        col_citas = citas.filter(estatus_cita__in=col["statuses"])
        groups = {}
        for c in col_citas:
            key = c.estatus_seguimiento or "Sin seguimiento"
            groups.setdefault(key, []).append(c)

        grouped = []
        for status in seguimiento_order:
            items = groups.get(status)
            if not items:
                continue
            grouped.append(
                {
                    "seguimiento": status,
                    "items": items,
                    "card_count": len(items),
                }
            )

        kanban_data.append(
            {
                "title": col["title"],
                "status_class": col["class"],
                "groups": grouped,
                "card_count": col_citas.count(),
            }
        )

    return kanban_data, total_citas, total_atendidas, total_cerradas


def citas_kanban(request):
    citas, fecha_desde, fecha_hasta = _filter_citas_queryset(request)
    kanban_data, total_citas, total_atendidas, total_cerradas = _build_citas_kanban_data(citas)
    context = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "total_citas": total_citas,
        "total_atendidas": total_atendidas,
        "total_cerradas": total_cerradas,
        "kanban_data": kanban_data,
    }
    return render(request, "comercial/kanban.html", context)


def citas_kanban_resumen_pdf(request):
    citas, fecha_desde, fecha_hasta = _filter_citas_queryset(request)
    kanban_data, total_citas, total_atendidas, total_cerradas = _build_citas_kanban_data(citas)

    if fecha_desde or fecha_hasta:
        desde_txt = (
            datetime.strptime(fecha_desde, "%Y-%m-%d").strftime("%d/%m/%Y")
            if fecha_desde
            else "???"
        )
        hasta_txt = (
            datetime.strptime(fecha_hasta, "%Y-%m-%d").strftime("%d/%m/%Y")
            if fecha_hasta
            else "???"
        )
    else:
        fechas = citas.aggregate(min_fecha=Min("fecha_cita"), max_fecha=Max("fecha_cita"))
        min_fecha = fechas.get("min_fecha")
        max_fecha = fechas.get("max_fecha")
        desde_txt = min_fecha.strftime("%d/%m/%Y") if min_fecha else "—"
        hasta_txt = max_fecha.strftime("%d/%m/%Y") if max_fecha else "—"
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
    body_style = ParagraphStyle(
        "BodySmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        wordWrap="LTR",
        splitLongWords=0,
    )
    number_style = ParagraphStyle(
        "TotalsNumber",
        parent=styles["BodyText"],
        fontSize=18,
        leading=18,
        alignment=1,
        spaceBefore=0,
        spaceAfter=0,
    )

    elements = [
        Paragraph("Resumen de Citas", title_style),
        Paragraph(subtitle_text, subtitle_style),
        Spacer(1, 8),
    ]

    page_width = pagesize[0]
    available_width = page_width - doc.leftMargin - doc.rightMargin
    totals_table = Table(
        [
            ["Total citas", "Atendidas", "Cerrados"],
            [
                Paragraph(str(total_citas), number_style),
                Paragraph(str(total_atendidas), number_style),
                Paragraph(str(total_cerradas), number_style),
            ],
        ],
        colWidths=[available_width / 3] * 3,
        rowHeights=[22, 30],
    )
    totals_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b313f")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8fbff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#59b9c7")),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#003b71")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("FONTSIZE", (0, 1), (-1, 1), 18),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#aebed2")),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 0), (-1, 0), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
            ]
        )
    )
    elements.append(totals_table)
    elements.append(Spacer(1, 10))
    totals_separator = Table([[""]], colWidths=[available_width * 0.9])
    totals_separator.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 1.2, colors.HexColor("#2b313f")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    elements.append(totals_separator)
    elements.append(Spacer(1, 12))

    col_widths = [
        available_width * 0.18,
        available_width * 0.23,
        available_width * 0.17,
        available_width * 0.12,
        available_width * 0.14,
        available_width * 0.16,
    ]

    header_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.90, 0.93, 0.96, alpha=0.3)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2a3d")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#aebed2")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )

    block_by_title = {b["title"]: b for b in kanban_data}
    ordered_titles = ["Atendidas", "Agendadas", "Canceladas"]
    block_colors = {
        "Atendidas": colors.HexColor("#b8d9b3"),
        "Agendadas": colors.HexColor("#f5e2a8"),
        "Canceladas": colors.HexColor("#f3b0b0"),
    }

    for idx, title in enumerate(ordered_titles):
        bloque = block_by_title.get(title)
        if not bloque:
            continue
        elements.append(Spacer(1, 6))
        all_items = []
        for grupo in bloque["groups"]:
            all_items.extend(grupo["items"])
        table_data = [
            [
                f"{bloque['title']}",
                "",
                "",
                "",
                "",
                f"Total: {bloque['card_count']}",
            ],
            [
                "Fecha",
                "Prospecto",
                "Servicio",
                "N?mero cita",
                "Vendedor",
                "Estatus seguimiento",
            ]
        ]
        for item in all_items:
            table_data.append(
                [
                    item.fecha_cita.strftime("%d/%m/%Y %H:%M") if item.fecha_cita else "",
                    Paragraph(item.prospecto or "", body_style),
                    Paragraph(item.servicio or "", body_style),
                    item.numero_cita or "",
                    Paragraph(item.vendedor or "", body_style),
                    Paragraph(item.estatus_seguimiento or "", body_style),
                ]
            )
        table = Table(table_data, colWidths=col_widths, repeatRows=2)
        table_style = TableStyle(list(header_style.getCommands()))
        table_style.add("SPAN", (0, 0), (4, 0))
        table_style.add("ALIGN", (0, 0), (4, 0), "CENTER")
        table_style.add("ALIGN", (5, 0), (5, 0), "CENTER")
        table_style.add("ALIGN", (0, 1), (-1, 1), "CENTER")
        table_style.add("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
        table_style.add("FONTSIZE", (0, 0), (-1, 0), 10)
        table_style.add("WORDWRAP", (0, 0), (-1, -1), True)
        header_color = block_colors.get(bloque["title"])
        if header_color:
            darker = colors.Color(
                max(header_color.red - 0.18, 0),
                max(header_color.green - 0.18, 0),
                max(header_color.blue - 0.18, 0),
            )
            darker_text = colors.Color(
                max(header_color.red - 0.55, 0),
                max(header_color.green - 0.55, 0),
                max(header_color.blue - 0.55, 0),
            )
            table_style.add("BACKGROUND", (0, 0), (-1, 0), darker)
            table_style.add("TEXTCOLOR", (0, 0), (-1, 0), darker_text)
            table_style.add("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#b7c7d9"))
            table_style.add("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#1f2a3d"))
            table_style.add("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold")
        table.setStyle(table_style)
        elements.append(table)
        is_last_table = idx == len(ordered_titles) - 1
        if not is_last_table:
            elements.append(Spacer(1, 14))
            separator = Table([[""]], colWidths=[available_width * 0.9])
            separator.setStyle(
                TableStyle(
                    [
                        ("LINEBELOW", (0, 0), (-1, -1), 1.2, colors.HexColor("#2b313f")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            elements.append(separator)
            elements.append(Spacer(1, 14))

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
    response["Content-Disposition"] = 'inline; filename="resumen_citas.pdf"'
    return response


def agregar_cita(request):
    back_url = request.GET.get("next") or reverse("comercial_cita_list")
    copy_from = request.GET.get("copy_from")
    initial_data = {}
    if copy_from:
        origen = get_object_or_404(Cita, pk=copy_from)
        initial_data = _initial_desde_cita(origen)
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = CitaForm(initial=initial_data)

    context = {"form": form, "back_url": back_url}
    return render(request, "comercial/form.html", context)


def editar_cita(request, id: int):
    back_url = request.GET.get("next") or reverse("comercial_cita_list")
    cita = get_object_or_404(Cita, pk=id)
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            cita = form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = CitaForm(instance=cita)

    context = {"form": form, "back_url": back_url}
    return render(request, "comercial/form.html", context)


def eliminar_cita(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("comercial_cita_list")
    cita = get_object_or_404(Cita, pk=id)
    cita.delete()
    return redirect(back_url)


def reportes_dashboard(request):
    return render(request, "comercial/reportes.html")


def control_comercial(request):
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
    return render(request, "comercial/control.html", context)


def comercial_kpi_create(request):
    back_url = request.GET.get("next") or reverse("comercial_control")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ComercialKpiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ComercialKpiForm()
    return render(request, "comercial/kpi_form.html", {"form": form, "back_url": back_url})


def comercial_kpi_update(request, pk: int):
    kpi = get_object_or_404(ComercialKpi, pk=pk)
    back_url = request.GET.get("next") or reverse("comercial_control")
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
        "comercial/kpi_form.html",
        {"form": form, "back_url": back_url, "kpi": kpi},
    )


def comercial_kpi_delete(request, pk: int):
    back_url = request.POST.get("next") or reverse("comercial_control")
    kpi = get_object_or_404(ComercialKpi, pk=pk)
    kpi.delete()
    return redirect(back_url)


def comercial_meta_create(request):
    back_url = request.GET.get("next") or reverse("comercial_control")
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
        "comercial/meta_form.html",
        {
            "form": form,
            "back_url": back_url,
            "mes": initial.get("mes"),
            "anio": initial.get("anio"),
            "mes_nombre": mes_nombre,
        },
    )


def comercial_meta_update(request, pk: int):
    meta = get_object_or_404(ComercialKpiMeta, pk=pk)
    back_url = request.GET.get("next") or reverse("comercial_control")
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
        "comercial/meta_form.html",
        {
            "form": form,
            "back_url": back_url,
            "meta": meta,
            "mes": meta.mes,
            "anio": meta.anio,
            "mes_nombre": mes_nombre,
        },
    )


def comercial_meta_delete(request, pk: int):
    back_url = request.POST.get("next") or reverse("comercial_control")
    meta = get_object_or_404(ComercialKpiMeta, pk=pk)
    meta.delete()
    return redirect(back_url)
