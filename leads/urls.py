from django.urls import path
from .views import meta_lead_webhook

urlpatterns = [
    path("webhooks/meta/lead/", meta_lead_webhook, name="meta_lead_webhook"),
]