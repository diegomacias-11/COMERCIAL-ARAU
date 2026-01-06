from django.contrib import admin

from .models import ActividadExp


@admin.register(ActividadExp)
class ActividadExpAdmin(admin.ModelAdmin):
    list_display = (
        "tarea",
        "tipo",
        "area",
        "estilo",
        "fecha_solicitud_exp",
        "fecha_solicitud_mkt",
        "fecha_entrega_mkt",
        "comunicado_aviso",
        "estatus_envio",
        "fecha_envio",
    )
    list_filter = ("tipo", "area", "comunicado_aviso", "estatus_envio")
    search_fields = ("tarea", "notas", "url")

# Register your models here.
