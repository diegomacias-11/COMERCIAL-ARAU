from django.db import models

class MetaLead(models.Model):
    # === Core Meta (fijo) ===
    leadgen_id = models.CharField(max_length=100, unique=True)  # id
    created_time = models.DateTimeField()

    ad_id = models.CharField(max_length=50)
    ad_name = models.CharField(max_length=200)

    adset_id = models.CharField(max_length=50)
    adset_name = models.CharField(max_length=200)

    campaign_id = models.CharField(max_length=50)
    campaign_name = models.CharField(max_length=200)

    form_id = models.CharField(max_length=50)
    form_name = models.CharField(max_length=200)

    is_organic = models.BooleanField(default=False)
    platform = models.CharField(max_length=50)

    # === Campos comunes (si existen) ===
    full_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)

    # === Dinámico / universal ===
    raw_fields = models.JSONField(default=dict)   # preguntas del form
    raw_payload = models.JSONField(default=dict)  # respuesta completa Meta

    inserted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name or 'Lead'} - {self.campaign_name}"
