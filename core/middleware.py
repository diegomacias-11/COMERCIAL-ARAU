from __future__ import annotations

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import Permission
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils.http import urlencode


class GroupPermissionMiddleware(MiddlewareMixin):
    """
    Enforce CRUD permisos por grupo sin configurar vista por vista.
    Usa el nombre de la vista (url_name) y el modulo para construir el permiso
    estandar de Django: <app_label>.<action>_<model>.
    """

    _IGNORE = {
        "lista", "list", "agregar", "add", "editar", "update",
        "eliminar", "delete", "reporte", "reportes",
        "detalle", "detail", "ver",
    }

    REPORTS_ALLOWED = {
        "/comercial/reportes/": {"dirección comercial"},
        "/marketing/reportes/": set(),    # Completar cuando exista
        "/operaciones/reportes/": set(),  # Completar cuando exista
    }

    def _infer_action(self, url_name: str) -> str:
        lower = url_name.lower()
        if lower.startswith(("agregar", "add", "crear", "create", "nuevo", "nueva")):
            return "add"
        if lower.startswith(("editar", "update", "actualizar", "cambiar")):
            return "change"
        if lower.startswith(("eliminar", "delete", "borrar")):
            return "delete"
        return "view"

    def _infer_model(self, url_name: str) -> str:
        parts = [p for p in url_name.lower().split("_") if p]
        # Tomar el ultimo segmento que no sea de accion
        base = ""
        for part in reversed(parts):
            if part not in self._IGNORE:
                base = part
                break
        if not base and parts:
            base = parts[-1]

        # Ajustes manuales por app
        if "actividades_merca" in url_name:
            return "actividadmerca"
        if "comisiones" in parts:
            if "pago" in parts:
                return "pagocomision"
            return "comision"
        if "clientes" in parts or base == "clientes":
            return "cliente"

        # Singularizar de forma basica
        if base.endswith("es"):
            base = base[:-2]
        elif base.endswith("s"):
            base = base[:-1]
        return base

    def process_view(self, request, view_func, view_args, view_kwargs):

        # Excepcion: permitir webhooks externos (Meta, Stripe, etc.)
        if request.path.startswith("/webhooks/"):
            return None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        resolver = getattr(request, "resolver_match", None)
        if not resolver or not resolver.url_name:
            return None

        public_names = {"login", "logout", "inicio"}
        if resolver.url_name in public_names:
            return None

        # Control fino para reportes (no hay modelo en admin)
        for prefix, allowed_groups in self.REPORTS_ALLOWED.items():
            if request.path.startswith(prefix):
                if user.is_superuser:
                    return None
                if allowed_groups:
                    user_groups = {g.lower() for g in user.groups.values_list("name", flat=True)}
                    if user_groups & allowed_groups:
                        return None
                return HttpResponse(
                    "<script>alert('No tienes permisos para este reporte.'); window.history.back();</script>",
                    status=403,
                    content_type="text/html",
                )

        app_label = view_func.__module__.split(".")[0]
        action = self._infer_action(resolver.url_name)
        model = self._infer_model(resolver.url_name)

        if not model:
            return None

        perm_code = f"{app_label}.{action}_{model}"

        # Si no existe un permiso definido para este modelo/acción, no bloquear
        if not Permission.objects.filter(
            content_type__app_label=app_label,
            codename=f"{action}_{model}",
        ).exists():
            return None

        if user.has_perm(perm_code):
            return None

        return HttpResponse(
            "<script>alert('No tienes permisos.'); window.history.back();</script>",
            status=403,
            content_type="text/html",
        )


class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Redirige a login si el usuario no esta autenticado, salvo rutas publicas.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):

        # Excepcion: permitir webhooks externos
        if request.path.startswith("/webhooks/"):
            return None

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            resolver = getattr(request, "resolver_match", None)
            url_name = resolver.url_name if resolver else None
            # Redirigir a actividades_merca al ingresar (home) para grupos de marketing/diseño
            if url_name in {None, "", "root", "inicio"} or request.path == "/":
                if user.groups.filter(name__in=["Dirección Marketing", "Marketing", "Diseño"]).exists():
                    return HttpResponseRedirect("/actividades_merca/")
            return None

        resolver = getattr(request, "resolver_match", None)
        url_name = resolver.url_name if resolver else None
        public_names = {"login", "logout", "inicio"}

        path = request.path
        if (
            (url_name in public_names)
            or path.startswith(settings.STATIC_URL)
            or path.startswith("/admin")
        ):
            return None

        login_url = settings.LOGIN_URL
        next_param = urlencode({"next": request.get_full_path()})
        return HttpResponseRedirect(f"{login_url}?{next_param}")
