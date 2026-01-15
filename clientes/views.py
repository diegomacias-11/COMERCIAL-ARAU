from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, time

from django import forms
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from core.choices import SERVICIO_CHOICES
from .models import Cliente, Contacto
from alianzas.models import Alianza
import unicodedata


class ClienteForm(forms.ModelForm):
    comision_campos = [f"comision_{i}" for i in range(1, 11)]
    comisionista_campos = [f"comisionista_{i}" for i in range(1, 11)]

    class Meta:
        model = Cliente
        fields = [
            "cliente",
            "servicio",
            "giro",
            "tipo",
            "medio",
            "conexion",
            "domicilio",
            "pagina_web",
            "linkedin",
            "otra_red",
            "propuesta",
            *[f"comisionista_{i}" for i in range(1, 11)],
            *[f"comision_{i}" for i in range(1, 11)],
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.update({
            campo: self.fields[campo]
            for campo in self.comisionista_campos + self.comision_campos
            if campo in self.fields
        })
        # Ordenar alianzas por nombre (ya guardadas en uppercase/strip)
        alianza_qs = Alianza.objects.all().order_by("nombre")
        for campo in self.comisionista_campos:
            self.fields[campo].queryset = alianza_qs
            self.fields[campo].label = f"Comisionista {campo.split('_')[-1]}"
        # Mostrar valores porcentuales como enteros (precisión con Decimal)
        for campo in self.comision_campos:
            self.fields[campo].widget = forms.NumberInput(attrs={"step": "0.01", "min": "0"})
            self.fields[campo].label = f"Comisión {campo.split('_')[-1]} (%)"
            if self.initial.get(campo) is not None:
                try:
                    self.initial[campo] = (Decimal(self.initial[campo]) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                except Exception:
                    pass

        # Pasar fecha_registro para display en plantilla, igual que en comercial
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None) and self.instance.fecha_registro:
            self.fecha_registro_display = timezone.localtime(self.instance.fecha_registro)

    def clean(self):
        cleaned = super().clean()
        # Convertir porcentajes enteros a decimales (10 -> 0.10) con Decimal
        for campo in self.comision_campos:
            val = cleaned.get(campo)
            if val is not None:
                try:
                    cleaned[campo] = (Decimal(str(val)) / Decimal("100")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
                except Exception:
                    cleaned[campo] = val
        return cleaned

    @property
    def total_comision_porcentaje(self):
        data = getattr(self, "cleaned_data", {}) or {}
        total = 0
        for campo in self.comision_campos:
            val = data.get(campo)
            if val is None:
                continue
            try:
                total += float(Decimal(val) * Decimal("100"))
            except Exception:
                total += val * 100  # fallback si val ya es float
        return total


def _comision_pairs(form: ClienteForm):
    pairs = []
    for i in range(1, 11):
        ci = f"comisionista_{i}"
        cv = f"comision_{i}"
        if ci in form.fields and cv in form.fields:
            pairs.append((form[ci], form[cv]))
    return pairs


def _can_view_comisiones_inputs(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    names = [g.name for g in user.groups.all()]

    def _norm(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()

    normed = {_norm(name) for name in names}
    return "direccion comercial" in normed or "direccion operaciones" in normed


def clientes_lista(request):
    clientes = Cliente.objects.all().order_by("-fecha_registro")
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""
    nombre = (request.GET.get("cliente") or "").strip()
    servicio_sel = request.GET.get("servicio") or ""

    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(d, time.min), tz)
            clientes = clientes.filter(fecha_registro__gte=start_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(d, time.max), tz)
            clientes = clientes.filter(fecha_registro__lte=end_dt)
        except ValueError:
            pass
    if nombre:
        clientes = clientes.filter(cliente__icontains=nombre)
    if servicio_sel:
        clientes = clientes.filter(servicio=servicio_sel)
    context = {
        "clientes": clientes,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "cliente_nombre": nombre,
        "servicio_sel": servicio_sel,
        "servicio_choices": SERVICIO_CHOICES,
    }
    return render(request, "clientes/lista.html", context)


ContactoFormSet = inlineformset_factory(
    Cliente,
    Contacto,
    fields=["nombre", "telefono", "correo", "puesto"],
    extra=1,
    can_delete=True,
)


def agregar_cliente(request):
    back_url = request.GET.get("next") or reverse("clientes_cliente_list")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ClienteForm()

    contactos_url = None
    if getattr(form.instance, "pk", None):
        contactos_url = f"{reverse('clientes_contacto_list', args=[form.instance.pk])}?next={request.get_full_path()}"

    context = {
        "form": form,
        "back_url": back_url,
        "comisiones": _comision_pairs(form),
        "contactos_url": contactos_url,
        "can_view_comisiones_inputs": _can_view_comisiones_inputs(request.user),
    }
    return render(request, "clientes/form.html", context)


def editar_cliente(request, id: int):
    back_url = request.GET.get("next") or reverse("clientes_cliente_list")
    cliente = get_object_or_404(Cliente, pk=id)
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ClienteForm(instance=cliente)

    contactos_url = None
    if getattr(form.instance, "pk", None):
        contactos_url = f"{reverse('clientes_contacto_list', args=[form.instance.pk])}?next={request.get_full_path()}"

    context = {
        "form": form,
        "back_url": back_url,
        "comisiones": _comision_pairs(form),
        "contactos_url": contactos_url,
        "can_view_comisiones_inputs": _can_view_comisiones_inputs(request.user),
    }
    return render(request, "clientes/form.html", context)


def contactos_cliente(request, id: int):
    cliente = get_object_or_404(Cliente, pk=id)
    back_url = request.GET.get("next") or reverse("clientes_cliente_update", args=[id])
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        formset = ContactoFormSet(request.POST, instance=cliente)
        if formset.is_valid():
            formset.save()
            # Permanece en el directorio de contactos tras guardar
            stay_url = reverse("clientes_contacto_list", args=[cliente.pk])
            if back_url:
                stay_url = f"{stay_url}?next={back_url}"
            return redirect(stay_url)
    else:
        formset = ContactoFormSet(instance=cliente)

    context = {
        "cliente": cliente,
        "formset": formset,
        "back_url": back_url,
    }
    return render(request, "clientes/contactos.html", context)


def eliminar_cliente(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("clientes_cliente_list")
    cliente = get_object_or_404(Cliente, pk=id)
    cliente.delete()
    return redirect(back_url)


def eliminar_contacto(request, id: int):
    contacto = get_object_or_404(Contacto, pk=id)
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("clientes_contacto_list", args=[contacto.cliente_id])
    cliente_id = contacto.cliente_id
    contacto.delete()
    # Siempre regresa al directorio de contactos de ese cliente (o al back_url si viene en next)
    if back_url:
        return redirect(back_url)
    return redirect(reverse("clientes_contacto_list", args=[cliente_id]))
