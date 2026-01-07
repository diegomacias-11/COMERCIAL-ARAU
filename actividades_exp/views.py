from django import forms
from django.shortcuts import render, get_object_or_404, redirect

from core.choices import ACTIVIDADES_EXP_TIPO_CHOICES, ACTIVIDADES_EXP_AREA_CHOICES
from .models import ActividadExp


class ActividadExpForm(forms.ModelForm):
    class Meta:
        model = ActividadExp
        fields = [
            "tarea",
            "tipo",
            "area",
            "estilo",
            "fecha_solicitud_exp",
            "fecha_solicitud_mkt",
            "fecha_entrega_mkt",
            "comunicado_aviso",
            "url",
            "estatus_envio",
            "fecha_envio",
            "notas",
        ]
        widgets = {
            "fecha_solicitud_exp": forms.DateInput(attrs={"type": "date"}),
            "fecha_solicitud_mkt": forms.DateInput(attrs={"type": "date"}),
            "fecha_entrega_mkt": forms.DateInput(attrs={"type": "date"}),
            "fecha_envio": forms.DateInput(attrs={"type": "date"}),
            "tarea": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("tipo", "area", "estilo", "comunicado_aviso"):
            if name in self.fields:
                self.fields[name].empty_label = "----"


def actividades_exp_lista(request):
    qs = ActividadExp.objects.all().order_by("-fecha_solicitud_exp", "-creado")
    tipo_sel = request.GET.get("tipo") or ""
    area_sel = request.GET.get("area") or ""
    estatus_envio_sel = request.GET.get("estatus_envio") or ""

    if tipo_sel:
        qs = qs.filter(tipo=tipo_sel)
    if area_sel:
        qs = qs.filter(area=area_sel)
    if estatus_envio_sel in {"si", "no"}:
        qs = qs.filter(estatus_envio=(estatus_envio_sel == "si"))

    context = {
        "actividades": list(qs),
        "tipo_choices": ACTIVIDADES_EXP_TIPO_CHOICES,
        "area_choices": ACTIVIDADES_EXP_AREA_CHOICES,
        "tipo_sel": tipo_sel,
        "area_sel": area_sel,
        "estatus_envio_sel": estatus_envio_sel,
    }
    return render(request, "actividades_exp/lista.html", context)


def actividades_exp_kanban(request):
    qs = ActividadExp.objects.all().order_by("-fecha_solicitud_exp", "-creado")
    tipo_sel = request.GET.get("tipo") or ""
    area_sel = request.GET.get("area") or ""

    if tipo_sel:
        qs = qs.filter(tipo=tipo_sel)
    if area_sel:
        qs = qs.filter(area=area_sel)
    qs = qs.filter(estatus_envio=False)

    grouped = []
    by_area = {}
    for act in qs:
        area_key = act.area or "Sin área"
        tipo_key = act.tipo or "Sin tipo"
        by_area.setdefault(area_key, {}).setdefault(tipo_key, []).append(act)

    for area, tipos in by_area.items():
        grouped.append(
            {
                "area": area,
                "tipos": [{"nombre": tipo, "items": acts} for tipo, acts in tipos.items()],
            }
        )

    context = {
        "kanban_data": grouped,
        "tipo_choices": ACTIVIDADES_EXP_TIPO_CHOICES,
        "area_choices": ACTIVIDADES_EXP_AREA_CHOICES,
        "tipo_sel": tipo_sel,
        "area_sel": area_sel,
    }
    return render(request, "actividades_exp/kanban.html", context)


def crear_actividad_exp(request):
    back_url = request.GET.get("next") or "/actividades_exp/"
    if request.method == "POST":
        form = ActividadExpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ActividadExpForm()
    return render(request, "actividades_exp/form.html", {"form": form, "back_url": back_url})


def editar_actividad_exp(request, pk: int):
    actividad = get_object_or_404(ActividadExp, pk=pk)
    back_url = request.GET.get("next") or "/actividades_exp/"
    if request.method == "POST":
        form = ActividadExpForm(request.POST, instance=actividad)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = ActividadExpForm(instance=actividad)
    return render(
        request,
        "actividades_exp/form.html",
        {"form": form, "back_url": back_url, "actividad": actividad},
    )


def eliminar_actividad_exp(request, pk: int):
    actividad = get_object_or_404(ActividadExp, pk=pk)
    back_url = request.POST.get("next") or request.GET.get("next") or "/actividades_exp/"
    if not request.user.has_perm("actividades_exp.delete_actividadexp"):
        return render(
            request,
            "actividades_exp/form.html",
            {
                "form": ActividadExpForm(instance=actividad),
                "back_url": back_url,
                "actividad": actividad,
                "errors": {"permiso": "No tienes permisos para eliminar."},
            },
            status=403,
        )
    actividad.delete()
    return redirect(back_url)
