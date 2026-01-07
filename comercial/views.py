from datetime import datetime, time

from django import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.choices import SERVICIO_CHOICES
from .models import Cita, NUM_CITA_CHOICES


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
            "telefono",
            "correo",
            "conexion",
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
        "telefono": cita.telefono,
        "correo": cita.correo,
        "conexion": cita.conexion,
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
    context = {
        "citas": citas,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "prospecto": prospecto,
        "servicio": servicio,
        "servicio_choices": SERVICIO_CHOICES,
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
