from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

from .models import UserSessionActivity, UserActionLog

"""
Autoregistra todos los modelos instalados para que respeten los permisos
configurados en el admin sin tener que declararlos manualmente.
"""

_SKIP = {UserSessionActivity, UserActionLog}

for model in apps.get_models():
    if model in _SKIP:
        continue
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass


@admin.register(UserSessionActivity)
class UserSessionActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "last_seen", "ip_address", "user_agent")
    list_filter = ("user", "last_seen")
    search_fields = ("user__username", "session_key", "ip_address")
    ordering = ("-last_seen",)


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "method", "path", "status_code", "created_at")
    list_filter = ("method", "status_code", "created_at")
    search_fields = ("user__username", "path", "ip_address", "user_agent")
    ordering = ("-created_at",)
