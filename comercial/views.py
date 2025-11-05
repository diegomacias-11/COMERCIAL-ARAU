from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, time
from .models import Cita
from .sheets import append_cita_to_sheet, update_cita_in_sheet


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
    class Meta:
        model = Cita
        fields = [
            "prospecto",
            "giro",
            "tipo",
            "medio",
            "servicio",
            "servicio2",
            "servicio3",
            "contacto",
            "telefono",
            "conexion",
            "vendedor",
            "estatus_cita",
            "fecha_cita",
            "numero_cita",
            "estatus_seguimiento",
            "comentarios",
            "lugar",
        ]
        widgets = {
            # El widget lo definimos arriba con formato explícito
        }


def citas_lista(request):
    citas = Cita.objects.all().order_by("-fecha_cita")
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""

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
    context = {
        "citas": citas,
        # Contexto mínimo; dejamos valores para el filtro de fechas
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    return render(request, "comercial/lista.html", context)


def agregar_cita(request):
    back_url = request.GET.get("next") or reverse("citas_lista")
    if request.method == "POST":
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save()
            # Sincronizar a Google Sheets (append). Identificación por ID en columna A.
            try:
                append_cita_to_sheet(cita)
            except Exception:
                # Evitar romper flujo si falla la sincronización
                pass
            return redirect(request.POST.get("next") or back_url)
    else:
        form = CitaForm()

    context = {"form": form, "back_url": back_url}
    return render(request, "comercial/form.html", context)


def editar_cita(request, id: int):
    back_url = request.GET.get("next") or reverse("citas_lista")
    cita = get_object_or_404(Cita, pk=id)
    if request.method == "POST":
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            cita = form.save()
            # Sincronizar cambio en Google Sheets (update)
            try:
                update_cita_in_sheet(cita)
            except Exception:
                pass
            return redirect(request.POST.get("next") or back_url)
    else:
        form = CitaForm(instance=cita)

    context = {"form": form, "back_url": back_url}
    return render(request, "comercial/form.html", context)


def eliminar_cita(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("citas_lista")
    cita = get_object_or_404(Cita, pk=id)
    # Si se elimina, opcionalmente podríamos borrar del sheet; por ahora solo BD
    cita.delete()
    return redirect(back_url)

from django.http import JsonResponse
from .sheets import _get_service

def debug_sheets(request):
    try:
        service = _get_service()
        # Hacer una llamada muy ligera solo para confirmar conexión
        result = service.spreadsheets().get(spreadsheetId="TU_SPREADSHEET_ID").execute()
        title = result.get("properties", {}).get("title", "sin título")
        return JsonResponse({"status": "ok", "sheet_title": title})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})