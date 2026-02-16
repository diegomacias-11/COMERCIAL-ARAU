from django.urls import path
from .views import (
    lead_delete,
    lead_detail,
    leads_lista,
    leads_whatsapp_form,
    linkedin_lead_delete,
    linkedin_lead_detail,
    linkedin_lead_webhook,
    meta_lead_webhook,
)

urlpatterns = [
    path("", leads_lista, name="leads_metalead_list"),
    path("whatsapp/form/", leads_whatsapp_form, name="leads_metalead_whatsapp_form"),
    path("<int:pk>/", lead_detail, name="leads_metalead_detail"),
    path("<int:pk>/eliminar/", lead_delete, name="leads_metalead_delete"),
    path("linkedin/<int:pk>/", linkedin_lead_detail, name="leads_metalead_detail_linkedin"),
    path("linkedin/<int:pk>/eliminar/", linkedin_lead_delete, name="leads_metalead_delete_linkedin"),
    path("webhooks/meta/lead/", meta_lead_webhook, name="leads_metalead_webhook"),
    path("webhooks/linkedin/lead/", linkedin_lead_webhook, name="leads_linkedin_webhook"),
]
