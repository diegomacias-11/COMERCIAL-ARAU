from django.contrib import admin
from .models import MetaLead

@admin.register(MetaLead)
class MetaLeadAdmin(admin.ModelAdmin):
    list_display = (
        "leadgen_id",
        "campaign_name",
        "ad_name",
        "full_name",
        "email",
        "phone_number",
        "created_time",
    )
    search_fields = ("full_name", "email", "phone_number", "campaign_name")
    list_filter = ("campaign_name", "platform", "is_organic")
