from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Cliente._meta.fields]
    search_fields = [field.name for field in Cliente._meta.fields if field.get_internal_type() in ['CharField', 'TextField']]
    list_filter = ["tipo", "giro"]
    ordering = ("-fecha_registro",)