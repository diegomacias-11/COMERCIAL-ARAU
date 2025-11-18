from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "giro",
        "tipo",
        "contacto",
        "telefono",
        "conexion",
        "fecha_registro",
    )
    list_filter = ("tipo", "giro")
    search_fields = ("cliente", "contacto", "telefono", "conexion")
    ordering = ("-fecha_registro",)
