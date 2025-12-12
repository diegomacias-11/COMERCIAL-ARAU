from django.urls import path
from .views import meta_lead_webhook, leads_lista

urlpatterns = [
    path("leads/", leads_lista, name="leads_lista"),
    path("webhooks/meta/lead/", meta_lead_webhook, name="meta_lead_webhook"),
]
