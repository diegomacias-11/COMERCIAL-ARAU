from __future__ import annotations

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import Permission
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils.http import urlencode


class GroupPermissionMiddleware(MiddlewareMixin):
    """
    Enforce CRUD permisos por grupo sin configurar vista por vista.
    Usa el nombre de la vista (url_name) y el módulo para construir el permiso
    estándar de Django: <app_label>.<action>_<model>.
    """

    # Palabras a ignorar al intentar deducir el modelo desde el url_name
    _IGNORE = {"lista", "list", "agregar", "add", "editar", "update", "eliminar", "delete", "reporte", "reportes"}

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
        for part in reversed(parts):
            if part not in self._IGNORE:
                base = part
                break
        else:
            base = parts[-1] if parts else ""
        # singularizar suavemente (quitar solo una 's' final)
        if base.endswith("s"):
            base = base[:-1]
        return base

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        resolver = getattr(request, "resolver_match", None)
        if not resolver or not resolver.url_name:
            return None

        # Vistas públicas/comunitarias que no requieren permiso
        public_names = {"login", "logout", "inicio"}
        if resolver.url_name in public_names:
            return None

        app_label = view_func.__module__.split(".")[0]
        action = self._infer_action(resolver.url_name)
        model = self._infer_model(resolver.url_name)

        if not model:
            return None

        perm_code = f"{app_label}.{action}_{model}"
        # Si el permiso no existe en la BD, no bloqueamos.
        if not Permission.objects.filter(
            content_type__app_label=app_label,
            codename=f"{action}_{model}",
        ).exists():
            return None
        if user.has_perm(perm_code):
            return None

        # Sin permiso: responder con popup JS y volver atrás
        return HttpResponse(
            "<script>alert('No tienes permisos.'); window.history.back();</script>",
            status=403,
            content_type="text/html",
        )


class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Redirige a login si el usuario no está autenticado, salvo rutas públicas.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
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
