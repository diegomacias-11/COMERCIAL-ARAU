from django.urls import path
from .views import meta_lead_webhook, leads_lista

urlpatterns = [
    path("", leads_lista, name="leads_metalead_list"),
    path("webhooks/meta/lead/", meta_lead_webhook, name="leads_metalead_webhook"),
]
