from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Alianza


class AlianzaForm(forms.ModelForm):
    class Meta:
        model = Alianza
        fields = ["nombre", "telefono", "correo"]


def alianzas_lista(request):
    q = request.GET.get("q", "").strip()
    alianzas = Alianza.objects.all()
    if q:
        alianzas = alianzas.filter(nombre__icontains=q)
    return render(request, "alianzas/lista.html", {"alianzas": alianzas, "q": q})


def agregar_alianzas(request):
    back_url = request.GET.get("next") or reverse("alianzas_lista")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = AlianzaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = AlianzaForm()

    context = {"form": form, "back_url": back_url}
    return render(request, "alianzas/form.html", context)


def editar_alianzas(request, id: int):
    back_url = request.GET.get("next") or reverse("alianzas_lista")
    alianza = get_object_or_404(Alianza, pk=id)
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = AlianzaForm(request.POST, instance=alianza)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = AlianzaForm(instance=alianza)

    context = {"form": form, "back_url": back_url}
    return render(request, "alianzas/form.html", context)


def eliminar_alianzas(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("alianzas_lista")
    alianza = get_object_or_404(Alianza, pk=id)
    alianza.delete()
    return redirect(back_url)
