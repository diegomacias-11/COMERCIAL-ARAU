from django.contrib import admin
from .models import Alianza


@admin.register(Alianza)
class AlianzaAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Alianza._meta.fields]
    search_fields = [field.name for field in Alianza._meta.fields if field.get_internal_type() in ["CharField", "EmailField"]]
    list_filter = ["telefono", "correo"]
