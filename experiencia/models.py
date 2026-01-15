from django.db import models

from core.choices import EXPERIENCIA_PERIODICIDAD_CHOICES, CHAT_WELCOME_CHOICES, ESTATUS_CLIENTES_CHOICES


class ExperienciaCliente(models.Model):
    cliente_id = models.IntegerField(unique=True)
    cliente = models.CharField(max_length=150)
    servicio = models.CharField(max_length=100, blank=True, null=True)
    giro = models.CharField(max_length=150, blank=True, null=True)

    propuesta = models.URLField("Propuesta", blank=True, null=True)

    # Campos gestionados en experiencia
    nombre_comercial = models.CharField(max_length=200, blank=True, null=True)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    fecha_contrato = models.DateField(blank=True, null=True)
    periodicidad = models.CharField(
        max_length=20, choices=EXPERIENCIA_PERIODICIDAD_CHOICES, blank=True, null=True
    )
    chat_welcome = models.CharField(
        max_length=10, choices=CHAT_WELCOME_CHOICES, blank=True, null=True
    )
    meet = models.BooleanField(default=False)
    comentarios = models.TextField(blank=True, null=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CLIENTES_CHOICES, blank=True, null=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Cliente Experiencia"
        verbose_name_plural = "Clientes Experiencia"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return self.cliente
