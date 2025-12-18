from django.contrib import admin

from .forms import ActividadMercaForm
from .models import ActividadMerca


@admin.register(ActividadMerca)
class ActividadMercaAdmin(admin.ModelAdmin):
  list_display = ("cliente", "area", "fecha_inicio", "tarea", "dias", "mercadologo", "disenador", "fecha_fin", "estatus")
  list_filter = ("area", "mercadologo", "disenador", "evaluacion")
  search_fields = ("cliente", "tarea")
  form = ActividadMercaForm
