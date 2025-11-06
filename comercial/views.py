from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, time
from .models import Cita
from .sheets import append_cita_to_sheet, update_cita_in_sheet, delete_cita_from_sheet


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
            "servicio",
            "servicio2",
            "servicio3",
            "contacto",
            "telefono",
            "conexion",
            "medio",
            "estatus_cita",
            "fecha_cita",
            "numero_cita",
            "lugar",
            "estatus_seguimiento",
            "comentarios",
            "vendedor",
            "monto_factura",
        ]
        widgets = {
            # El widget lo definimos arriba con formato explÃ­cito
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
        # Contexto mÃ­nimo; dejamos valores para el filtro de fechas
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
            try:
                from .sheets import append_cita_to_sheet
                row = append_cita_to_sheet(cita)
            except Exception as e:
                import traceback
                print(f"❌ Error al enviar a Google Sheets: {e}")
                traceback.print_exc()
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
    # Borrar también del Google Sheet por ID
    try:
        delete_cita_from_sheet(cita.id)
    except Exception:
        pass
    cita.delete()
    return redirect(back_url)

