from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.contrib.admin.models import LogEntry
from django.utils import timezone
from django.utils.timezone import localtime

from .models import UserSessionActivity

"""
Autoregistra todos los modelos instalados para que respeten los permisos
configurados en el admin sin tener que declararlos manualmente.
Si un modelo ya está registrado (por un ModelAdmin personalizado), se omite.
"""

# Saltar modelos que no queremos mostrar
_SKIP_MODELS = {ContentType, Session, LogEntry}
_SKIP_LABELS = {"actividades_exp.ActividadExp"}

for model in apps.get_models():
    if model in _SKIP_MODELS:
        continue
    if model._meta.label in _SKIP_LABELS:
        continue
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass

# Reemplazar con un ModelAdmin personalizado para mostrar horario local
try:
    admin.site.unregister(UserSessionActivity)
except Exception:
    pass


@admin.register(UserSessionActivity)
class UserSessionActivityAdmin(admin.ModelAdmin):
    list_display = ("user_display", "last_action", "last_seen_local", "ip_address")
    list_filter = ("user",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "last_action", "last_path", "ip_address")
    ordering = ("-last_seen",)

    def user_display(self, obj):
        full_name = ""
        try:
            full_name = (obj.user.get_full_name() or "").strip()
        except Exception:
            full_name = ""
        return full_name if full_name else getattr(obj.user, "username", str(obj.user))

    user_display.short_description = "Usuario"

    def last_seen_local(self, obj):
        return localtime(obj.last_seen, timezone.get_current_timezone())

    last_seen_local.short_description = "Último acceso (local)"
