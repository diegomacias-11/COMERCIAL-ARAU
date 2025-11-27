from django.contrib import admin
from .models import Cita

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    # Mostrar TODAS las columnas automáticamente
    list_display = [field.name for field in Cita._meta.fields]

    # Filtros automáticos: solo campos con choices o campos tipo Char (except TextField)
    list_filter = [
        field.name for field in Cita._meta.fields
        if (field.choices or field.get_internal_type() in ["CharField", "DateTimeField"])
    ]

    # Campos buscables: todos los campos de texto
    search_fields = [
        field.name for field in Cita._meta.fields
        if field.get_internal_type() in ["CharField", "TextField"]
    ]

    # Orden por fecha de la cita (ya viene de tu Meta)
    ordering = ("-fecha_cita",)
