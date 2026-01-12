from django.contrib import admin

from .models import GastoMercadotecnia


@admin.register(GastoMercadotecnia)
class GastoMercadotecniaAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_facturacion",
        "categoria",
        "plataforma",
        "marca",
        "tdc",
        "tipo_facturacion",
        "periodicidad",
        "facturacion",
    )
    search_fields = ("marca", "categoria", "plataforma", "tdc")
    list_filter = ("categoria", "plataforma", "marca", "tipo_facturacion", "periodicidad")
