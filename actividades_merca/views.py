from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from .forms import _cliente_choices, ActividadMercaForm
from .models import ActividadMerca


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


def actividades_lista(request):
    qs = ActividadMerca.objects.all().order_by("-fecha_inicio")

    vista = (request.GET.get("vista") or "lista").lower()
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
    if mercadologo_sel:
        qs = qs.filter(mercadologo__in=[mercadologo_sel, "Todos"])
    if disenador_sel:
        qs = qs.filter(disenador__in=[disenador_sel, "Todos"])

    actividades = list(qs)
    # Recalcular estatus al vuelo para mantenerlo fresco
    for act in actividades:
        nuevo = act.calcular_estatus()
        if nuevo != act.estatus:
            act.estatus = nuevo
            act.save(update_fields=["estatus"])

    if estatus_sel:
        actividades = [a for a in actividades if a.estatus == estatus_sel]

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

    if vista == "kanban":
        # Agrupar por cliente y dentro por área
        grouped = []
        by_cliente = {}
        for act in actividades:
            try:
                compromiso = act.fecha_compromiso
                remaining = (compromiso - datetime.today().date()).days if compromiso else None
                act.dias_restantes = remaining if remaining is not None else ""
            except Exception:
                act.dias_restantes = ""
            key = (act.cliente or "").strip().upper()
            if key not in by_cliente:
                by_cliente[key] = {}
            area_key = act.area or "Sin área"
            by_cliente[key].setdefault(area_key, []).append(act)
        for cliente, areas in by_cliente.items():
            grouped.append(
                {
                    "cliente": cliente or "Sin cliente",
                    "areas": [{ "nombre": area, "items": acts } for area, acts in areas.items()],
                }
            )
        context["kanban_data"] = grouped
        return render(request, "actividades_merca/kanban.html", context)

    return render(request, "actividades_merca/lista.html", context)


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
