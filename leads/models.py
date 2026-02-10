from django.db import models
from core.choices import LEAD_ESTATUS_CHOICES, SERVICIO_CHOICES

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

    is_organic = models.BooleanField(default=False)
    platform = models.CharField(max_length=50)

    # === Campos comunes (si existen) ===
    full_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=150, blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)

    # === Control comercial ===
    contactado = models.BooleanField(default=False)
    estatus = models.CharField(max_length=30, choices=LEAD_ESTATUS_CHOICES, blank=True, null=True)
    servicio = models.CharField(max_length=100, choices=SERVICIO_CHOICES, blank=True, null=True)
    cita_agendada = models.DateTimeField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    cita = models.OneToOneField(
        "comercial.Cita",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="meta_lead",
    )

    # === Dinámico / universal ===
    raw_fields = models.JSONField(default=dict)   # preguntas del form
    raw_payload = models.JSONField(default=dict)  # respuesta completa Meta

    inserted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name or 'Lead'} - {self.campaign_name}"


class LinkedInLead(models.Model):
    lead_id = models.CharField(max_length=150, unique=True, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)

    ad_id = models.CharField(max_length=80, blank=True, null=True)
    ad_name = models.CharField(max_length=200, blank=True, null=True)
    adset_id = models.CharField(max_length=80, blank=True, null=True)
    adset_name = models.CharField(max_length=200, blank=True, null=True)
    campaign_id = models.CharField(max_length=80, blank=True, null=True)
    campaign_name = models.CharField(max_length=200, blank=True, null=True)
    form_id = models.CharField(max_length=80, blank=True, null=True)

    platform = models.CharField(max_length=50, default="linkedin")

    full_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=150, blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)

    contactado = models.BooleanField(default=False)
    estatus = models.CharField(max_length=30, choices=LEAD_ESTATUS_CHOICES, blank=True, null=True)
    servicio = models.CharField(max_length=100, choices=SERVICIO_CHOICES, blank=True, null=True)
    cita_agendada = models.DateTimeField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    cita = models.OneToOneField(
        "comercial.Cita",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="linkedin_lead",
    )

    raw_fields = models.JSONField(default=dict)
    raw_payload = models.JSONField(default=dict)

    inserted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name or 'LinkedIn Lead'} - {self.campaign_name or ''}".strip()
