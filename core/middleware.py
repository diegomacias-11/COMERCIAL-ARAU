from __future__ import annotations

from django.http import HttpResponse, HttpResponseRedirect
from django.apps import apps
from django.contrib.auth.models import Permission
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils.http import urlencode
import re

from .models import UserSessionActivity


class GroupPermissionMiddleware(MiddlewareMixin):
    """
    Enforce CRUD permisos por grupo sin configurar vista por vista.
    Usa el nombre de la vista (url_name) y el modulo para construir el permiso
    estandar de Django: <app_label>.<action>_<model>.
    """

    _IGNORE = {
        "lista", "list", "agregar", "add", "crear", "create", "editar", "update",
        "eliminar", "delete", "reporte", "reportes",
        "detalle", "detail", "ver",
    }

    REPORTS_ALLOWED = {
        "/comercial/reportes/": {"dirección comercial", "dirección operaciones", "apoyo comercial"},
        "/marketing/reportes/": {"dirección operaciones"},    # Completar cuando exista
        "/operaciones/reportes/": {"dirección operaciones"},  # Completar cuando exista
    }

    def _infer_action(self, url_name: str) -> str:
        lower = url_name.lower()
        tokens = [t for t in re.split(r"[_-]+", lower) if t]
        if any(t in {"eliminar", "delete", "borrar"} for t in tokens):
            return "delete"
        if any(t in {"editar", "update", "actualizar", "cambiar"} for t in tokens):
            return "change"
        if any(t in {"agregar", "add", "crear", "create", "nuevo", "nueva", "registrar"} for t in tokens):
            return "add"
        return "view"

    def _infer_model(self, url_name: str) -> str:
        def _tokenize(text: str) -> list[str]:
            cleaned = re.sub(r"[^a-z0-9_]+", " ", (text or "").lower())
            return [p for p in cleaned.replace("_", " ").split() if p]

        tokens = _tokenize(url_name)
        app_label = getattr(self, "_current_app_label", None)
        models = []
        if app_label:
            try:
                models = list(apps.get_app_config(app_label).get_models())
            except Exception:
                models = []

        if tokens and models:
            token_set = set(tokens)
            candidates = []
            for model in models:
                model_tokens = set()
                model_tokens.update(_tokenize(model._meta.model_name))
                model_tokens.update(_tokenize(model._meta.verbose_name))
                model_tokens.update(_tokenize(model._meta.verbose_name_plural))
                overlap = model_tokens & token_set
                if overlap:
                    candidates.append((len(overlap), model._meta.model_name))
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                return candidates[0][1]
            if len(models) == 1:
                return models[0]._meta.model_name

        parts = [p for p in (url_name or "").lower().split("_") if p]
        base = ""
        for part in reversed(parts):
            if part not in self._IGNORE:
                base = part
                break
        if not base and parts:
            base = parts[-1]

        if base.endswith("es"):
            base = base[:-2]
        elif base.endswith("s"):
            base = base[:-1]
        return base

    def process_view(self, request, view_func, view_args, view_kwargs):

        # Excepcion: permitir webhooks externos (Meta, Stripe, etc.)
        if request.path.startswith("/webhooks/") or request.path.startswith("/leads/webhooks/"):
            return None
        if request.path.startswith("/actividades_merca/solicitud/"):
            return None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        resolver = getattr(request, "resolver_match", None)
        if not resolver or not resolver.url_name:
            return None

        public_names = {"login", "logout", "core_inicio"}
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
        self._current_app_label = app_label
        action = self._infer_action(resolver.url_name)
        model = self._infer_model(resolver.url_name)
        self._current_app_label = None

        if not model:
            if action in {"add", "change", "delete"}:
                return HttpResponse(
                    "<script>alert('No tienes permisos.'); window.history.back();</script>",
                    status=403,
                    content_type="text/html",
                )
            return None

        perm_code = f"{app_label}.{action}_{model}"

        # Si no existe un permiso definido para este modelo/acción, no bloquear
        perm_exists = Permission.objects.filter(
            content_type__app_label=app_label,
            codename=f"{action}_{model}",
        ).exists()

        if action in {"add", "change", "delete"} and not perm_exists:
            return HttpResponse(
                "<script>alert('No tienes permisos.'); window.history.back();</script>",
                status=403,
                content_type="text/html",
            )

        if not perm_exists:
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
        if request.path.startswith("/webhooks/") or request.path.startswith("/leads/webhooks/"):
            return None

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            resolver = getattr(request, "resolver_match", None)
            url_name = resolver.url_name if resolver else None
            # Redirigir a actividades_merca al ingresar (home) para grupos de marketing/diseño
            if url_name in {None, "", "root", "core_inicio"} or request.path == "/":
                if user.groups.filter(name__in=["Dirección Marketing", "Marketing", "Diseño"]).exists():
                    return HttpResponseRedirect("/actividades_merca/")
                if user.groups.filter(name__in=["Dirección Marketing", "Diseño"]).exists():
                    return HttpResponseRedirect("/actividades_merca/")
                if user.groups.filter(name__in=["Apoyo Comercial"]).exists():
                    return HttpResponseRedirect("/comercial/citas/")
                if user.groups.filter(name__in=["Administración", "Dirección Comercial", "Dirección Operaciones", "Dirección"]).exists():
                    return HttpResponseRedirect("/ventas/")
                if user.groups.filter(name__in=["Experiencia"]).exists():
                    return HttpResponseRedirect("/actividades_exp/")
            return None

        resolver = getattr(request, "resolver_match", None)
        url_name = resolver.url_name if resolver else None
        public_names = {"login", "logout", "core_inicio"}

        path = request.path
        if (
            (url_name in public_names)
            or path.startswith(settings.STATIC_URL)
            or path.startswith("/admin")
            or path.startswith("/actividades_merca/solicitud/")
        ):
            return None

        login_url = settings.LOGIN_URL
        next_param = urlencode({"next": request.get_full_path()})
        return HttpResponseRedirect(f"{login_url}?{next_param}")


class ActivityLogMiddleware(MiddlewareMixin):
    """
    Registra últimas sesiones (solo usuarios autenticados).
    - UserSessionActivity: mantiene last_seen por session_key.
    """

    def _get_ip(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _last_action_label(self, request) -> str:
        resolver = getattr(request, "resolver_match", None)
        url_name = resolver.url_name if resolver else None
        if not url_name:
            return f"Visitó {request.path}"
        parts = [p for p in url_name.replace("-", "_").split("_") if p]
        label_map = {
            "actividades": "Actividades",
            "merca": "Actividades",
            "actividades_merca": "Actividades",
            "comisiones": "Comisiones",
            "comision": "Comisiones",
            "pagocomision": "Pago comisión",
            "pago": "Pago comisión",
            "ventas": "Ventas",
            "venta": "Ventas",
            "clientes": "Clientes",
            "cliente": "Clientes",
            "alianzas": "Alianzas",
            "alianza": "Alianzas",
            "leads": "Leads",
            "lead": "Leads",
            "citas": "Citas",
            "cita": "Citas",
            "reportes": "Reportes",
            "reporte": "Reportes",
            "experiencia": "Experiencia",
            "contactos": "Contactos",
            "contacto": "Contactos",
        }
        name = ""
        for part in parts:
            if part in label_map:
                name = label_map[part]
                break
        if not name:
            name = url_name.replace("_", " ").strip()
        lower = url_name.lower()
        if lower.startswith(("agregar", "add", "crear", "create", "nuevo", "nueva")):
            return f"Agregó {name}"
        if lower.startswith(("editar", "update", "actualizar", "cambiar")):
            return f"Editó {name}"
        if lower.startswith(("eliminar", "delete", "borrar")):
            return f"Eliminó {name}"
        if lower.startswith(("detalle", "detail", "ver")):
            return f"Vio {name}"
        return f"Visitó {name}"

    def process_response(self, request, response):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            if request.path.startswith(settings.STATIC_URL):
                return response
            session_key = getattr(request, "session", None) and request.session.session_key
            if session_key:
                last_action = self._last_action_label(request)
                last_path = request.path[:200]
                last_method = request.method[:10]
                # Usa el registro más reciente del usuario (si existe) y elimina duplicados
                qs = UserSessionActivity.objects.filter(user=user).order_by("-last_seen")
                activity = qs.first()
                if activity is None:
                    UserSessionActivity.objects.create(
                        user=user,
                        session_key=session_key,
                        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                        ip_address=self._get_ip(request),
                        last_action=last_action,
                        last_path=last_path,
                        last_method=last_method,
                    )
                else:
                    activity.session_key = session_key
                    activity.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
                    activity.ip_address = self._get_ip(request)
                    activity.last_action = last_action
                    activity.last_path = last_path
                    activity.last_method = last_method
                    activity.save(update_fields=["session_key", "user_agent", "ip_address", "last_action", "last_path", "last_method", "last_seen"])
                    # elimina otros registros del mismo usuario
                    UserSessionActivity.objects.filter(user=user).exclude(pk=activity.pk).delete()
        return response
