from datetime import datetime, date
from io import BytesIO
from django.db.models import Q
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from PyPDF2 import PdfReader, PdfWriter
import copy
from django.conf import settings

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import _cliente_choices, ActividadMercaForm
from .models import ActividadMerca, _business_days_between


ESTATUS_CHOICES = [
    "En tiempo",
    "Vence hoy",
    "Se entregó tarde",
    "Entregada a tiempo",
]


def _parse_date(val: str | None):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        return None


def _filtered_actividades(request, vista: str):
    qs = ActividadMerca.objects.all().order_by("-fecha_inicio")

    f_desde = _parse_date(request.GET.get("fecha_inicio"))
    f_hasta = _parse_date(request.GET.get("fecha_fin"))
    cliente_sel = request.GET.get("cliente") or ""
    estatus_sel = request.GET.get("estatus") or ""
    mercadologo_sel = request.GET.get("mercadologo") or ""
    disenador_sel = request.GET.get("disenador") or ""

    if vista == "kanban":
        qs = qs.filter(fecha_fin__isnull=True)

    if vista == "lista" and f_desde:
        qs = qs.filter(fecha_inicio__gte=f_desde)
    if vista == "lista" and f_hasta:
        qs = qs.filter(fecha_inicio__lte=f_hasta)
    if cliente_sel:
        qs = qs.filter(cliente__iexact=cliente_sel)
    if mercadologo_sel == "__none__":
        qs = qs.filter(Q(mercadologo__isnull=True) | Q(mercadologo=""))
    elif mercadologo_sel:
        qs = qs.filter(mercadologo__in=[mercadologo_sel, "Todos"])
    if disenador_sel == "__none__":
        qs = qs.filter(Q(disenador__isnull=True) | Q(disenador=""))
    elif disenador_sel:
        qs = qs.filter(disenador__in=[disenador_sel, "Todos"])

    actividades = list(qs)
    for act in actividades:
        nuevo = act.calcular_estatus()
        if nuevo != act.estatus:
            act.estatus = nuevo
            act.save(update_fields=["estatus"])

    if estatus_sel:
        actividades = [a for a in actividades if a.estatus == estatus_sel]

    filtros = {
        "f_desde": f_desde,
        "f_hasta": f_hasta,
        "cliente_sel": cliente_sel,
        "estatus_sel": estatus_sel,
        "mercadologo_sel": mercadologo_sel,
        "disenador_sel": disenador_sel,
    }
    return actividades, filtros


def actividades_lista(request):
    vista = (request.GET.get("vista") or "lista").lower()
    actividades, filtros = _filtered_actividades(request, vista)
    f_desde = filtros["f_desde"]
    f_hasta = filtros["f_hasta"]
    cliente_sel = filtros["cliente_sel"]
    estatus_sel = filtros["estatus_sel"]
    mercadologo_sel = filtros["mercadologo_sel"]
    disenador_sel = filtros["disenador_sel"]

    context = {
        "actividades": actividades,
        "clientes_choices": _cliente_choices(),
        "estatus_choices": ESTATUS_CHOICES,
        "mercadologo_choices": [(v, l) for v, l in ActividadMerca._meta.get_field("mercadologo").choices if v != "Todos"],
        "disenador_choices": [(v, l) for v, l in ActividadMerca._meta.get_field("disenador").choices if v != "Todos"],
        "f_desde": request.GET.get("fecha_inicio", ""),
        "f_hasta": request.GET.get("fecha_fin", ""),
        "cliente_sel": cliente_sel,
        "estatus_sel": estatus_sel,
        "mercadologo_sel": mercadologo_sel,
        "disenador_sel": disenador_sel,
        "vista": vista,
    }

    context["show_unassigned_warning"] = any(
        (not getattr(a, "mercadologo")) and (not getattr(a, "disenador"))
        for a in actividades
    )

    if vista == "kanban":
        status_order = ["Se entregó tarde", "Vence hoy", "En tiempo"]
        by_status = {}
        today = timezone.now().date()

        def _normalize_status(value: str) -> str:
            val = (value or "").strip()
            val = val.replace("Se entregÃ³ tarde", "Se entregó tarde")
            val = val.replace("Se entreg? tarde", "Se entregó tarde")
            val = val.replace("Se entrego tarde", "Se entregó tarde")
            return val

        for act in actividades:
            try:
                compromiso = act.fecha_compromiso
                remaining = _business_days_between(today, compromiso) if compromiso else None
            except Exception:
                remaining = None

            if remaining is None:
                act.dias_label = ""
                act.dias_value = ""
            elif remaining < 0:
                act.dias_label = "Días atrasados"
                act.dias_value = str(abs(remaining))
            else:
                act.dias_label = "Días restantes"
                act.dias_value = str(remaining)

            responsables = []
            for name in [act.mercadologo, act.disenador]:
                if name and name != "Todos":
                    responsables.append(name)
            act.responsables = " / ".join(responsables) if responsables else "Sin asignar"

            status_key = _normalize_status(act.estatus or "Sin estatus")
            if status_key == "Entregada a tiempo":
                continue
            client_key = (act.cliente or "").strip().upper() or "Sin cliente"
            area_key = act.area or "Sin área"

            by_status.setdefault(status_key, {})
            by_status[status_key].setdefault(client_key, {})
            by_status[status_key][client_key].setdefault(area_key, []).append(act)

        columns = []
        status_class_map = {
            "En tiempo": "status-in-time",
            "Vence hoy": "status-due-today",
            "Se entregó tarde": "status-late",
        }

        for status_name in status_order:
            clients = []
            total_col = 0
            for client_name, areas in by_status.get(status_name, {}).items():
                area_blocks = []
                total_client = 0
                for area_name, items in areas.items():
                    total_client += len(items)
                    area_blocks.append(
                        {
                            "nombre": area_name,
                            "items": items,
                            "count": len(items),
                        }
                    )
                total_col += total_client
                clients.append(
                    {
                        "cliente": client_name,
                        "total": total_client,
                        "areas": area_blocks,
                    }
                )
            columns.append(
                {
                    "status": status_name,
                    "total": total_col,
                    "status_class": status_class_map.get(status_name, ""),
                    "clients": clients,
                }
            )

        context["kanban_columns"] = columns
        return render(request, "actividades_merca/kanban.html", context)

    return render(request, "actividades_merca/lista.html", context)

def reporte_actividades(request):
    actividades, filtros = _filtered_actividades(request, "lista")
    f_desde = filtros["f_desde"]
    f_hasta = filtros["f_hasta"]
    cliente_sel = filtros["cliente_sel"] or "Todos"

    title_text = f"Reporte de actividades - Cliente: {cliente_sel}"
    if f_desde or f_hasta:
        desde_txt = f_desde.strftime("%d/%m/%Y") if f_desde else "—"
        hasta_txt = f_hasta.strftime("%d/%m/%Y") if f_hasta else "—"
        subtitle_text = f"Fechas: {desde_txt} a {hasta_txt}"
    else:
        subtitle_text = "Fechas: —"

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
        Spacer(1, 12),
    ]

    table_data = [
        [
            "Cliente",
            "Área",
            "Fecha inicio",
            "Tarea",
        ]
    ]
    for a in actividades:
        table_data.append(
            [
                Paragraph(a.cliente or "", body_style),
                Paragraph(a.area or "", body_style),
                a.fecha_inicio.strftime("%d/%m/%Y") if a.fecha_inicio else "",
                Paragraph(a.tarea or "", body_style),
            ]
        )

    page_width = pagesize[0]
    available_width = page_width - doc.leftMargin - doc.rightMargin
    col_widths = [
        available_width * 0.2,
        available_width * 0.15,
        available_width * 0.15,
        available_width * 0.5,
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
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("WORDWRAP", (0, 0), (-1, -1), True),
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
    response["Content-Disposition"] = 'inline; filename="reporte_actividades.pdf"'
    return response


def solicitud_publica(request):
    cliente_options = ["ENROK", "ARAU", "HUNTERLOOP"]
    errors = {}
    success = False
    initial = {
        "cliente": request.POST.get("cliente", ""),
        "tipo": request.POST.get("tipo", ""),
        "formato": request.POST.get("formato", ""),
        "mensaje": request.POST.get("mensaje", ""),
        "url": request.POST.get("url", ""),
        "fecha_entrega": request.POST.get("fecha_entrega", ""),
        "quien": request.POST.get("quien", ""),
        "departamento": request.POST.get("departamento", ""),
    }

    if request.method == "POST":
        cliente = (request.POST.get("cliente") or "").strip().upper()
        tipo = (request.POST.get("tipo") or "").strip()
        formato = (request.POST.get("formato") or "").strip()
        mensaje = (request.POST.get("mensaje") or "").strip()
        url = (request.POST.get("url") or "").strip()
        fecha_entrega_raw = (request.POST.get("fecha_entrega") or "").strip()
        quien = (request.POST.get("quien") or "").strip()
        departamento = (request.POST.get("departamento") or "").strip()

        # Validaciones
        if cliente not in cliente_options:
            errors["cliente"] = "Selecciona un cliente válido."
        if not tipo:
            errors["tipo"] = "Campo requerido."
        if not formato:
            errors["formato"] = "Campo requerido."
        if not mensaje:
            errors["mensaje"] = "Campo requerido."
        if not fecha_entrega_raw:
            errors["fecha_entrega"] = "Campo requerido."
        if not quien:
            errors["quien"] = "Campo requerido."
        if not departamento:
            errors["departamento"] = "Campo requerido."

        fecha_entrega = None
        if fecha_entrega_raw:
            try:
                fecha_entrega = datetime.strptime(fecha_entrega_raw, "%Y-%m-%d").date()
            except ValueError:
                errors["fecha_entrega"] = "Fecha inválida (YYYY-MM-DD)."

        if not errors:
            hoy = timezone.now().date()
            dias = 0
            if fecha_entrega and fecha_entrega > hoy:
                dias = _business_days_between(hoy, fecha_entrega) or 0
            # Construir tarea
            tarea_parts = [
                f"Tipo: {tipo}",
                f"Formato: {formato}",
                f"Mensaje: {mensaje}",
                f"Quién solicita: {quien}",
                f"Departamento: {departamento}",
            ]
            tarea_text = " | ".join(tarea_parts)
            ActividadMerca.objects.create(
                cliente=cliente,
                area="Internas",
                fecha_inicio=hoy,
                tarea=tarea_text,
                url=url or None,
                dias=dias,
                mercadologo=None,
                disenador=None,
                fecha_fin=None,
            )
            success = True
            initial = {
            "cliente": "",
            "tipo": "",
            "formato": "",
            "mensaje": "",
            "url": "",
            "fecha_entrega": "",
            "quien": "",
            "departamento": "",
        }

    return render(
        request,
        "actividades_merca/solicitud_publica.html",
        {
            "cliente_options": cliente_options,
            "errors": errors,
            "success": success,
            **initial,
        },
    )


def crear_actividad(request):
    back_url = request.GET.get("next") or "/actividades_merca/"
    if request.method == "POST":
        form = ActividadMercaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ActividadMercaForm(user=request.user)
    return render(
        request,
        "actividades_merca/form.html",
        {
            "form": form,
            "back_url": back_url,
        },
    )


def editar_actividad(request, pk: int):
    actividad = get_object_or_404(ActividadMerca, pk=pk)
    back_url = request.GET.get("next") or "/actividades_merca/"
    if request.method == "POST":
        form = ActividadMercaForm(request.POST, instance=actividad, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ActividadMercaForm(instance=actividad, user=request.user)
    return render(
        request,
        "actividades_merca/form.html",
        {
            "form": form,
            "back_url": back_url,
            "actividad": actividad,
        },
    )


def eliminar_actividad(request, pk: int):
    back_url = request.POST.get("next") or request.GET.get("next") or "/actividades_merca/"
    actividad = get_object_or_404(ActividadMerca, pk=pk)
    if not request.user.has_perm("actividades_merca.delete_actividadmerca"):
        return HttpResponse(
            "<script>alert('No tienes permisos para eliminar.'); window.history.back();</script>",
            status=403,
            content_type="text/html",
        )
    actividad.delete()
    return redirect(back_url)
