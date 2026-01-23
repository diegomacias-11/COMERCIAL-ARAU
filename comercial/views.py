from datetime import datetime, time

from django import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

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
