from django.shortcuts import render, redirect


def inicio(request):
    return render(request, "base.html")


def root_redirect(request):
    """Entra al login si no está autenticado; si ya inició, va a su sección según grupo."""
    if not request.user.is_authenticated:
        return redirect("login")

    first_group = request.user.groups.first()
    group_name = (first_group.name.lower() if first_group else "").strip()

    if "experiencia" in group_name:
        return redirect("experiencia_experienciacliente_list")
    if "marketing" in group_name:
        return redirect("actividades_merca_actividad_list")
    if "operaciones" in group_name:
        return redirect("alianzas_alianza_list")
    if "comercial" in group_name:
        return redirect("comercial_cita_list")

    return redirect("comercial_cita_list")


def csrf_failure(request, reason=""):
    return render(
        request,
        "errors/csrf.html",
        {"reason": reason},
        status=403,
    )
