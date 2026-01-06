from django.db import models

from core.choices import (
    ACTIVIDADES_EXP_TIPO_CHOICES,
    ACTIVIDADES_EXP_AREA_CHOICES,
    ACTIVIDADES_EXP_ESTILO_CHOICES,
    ACTIVIDADES_EXP_COMUNICADO_CHOICES,
)


class ActividadExp(models.Model):
    tarea = models.CharField(max_length=200, blank=True, null=True)
    tipo = models.CharField(max_length=50, choices=ACTIVIDADES_EXP_TIPO_CHOICES, blank=True, null=True)
    area = models.CharField(max_length=50, choices=ACTIVIDADES_EXP_AREA_CHOICES, blank=True, null=True)
    estilo = models.CharField(max_length=50, choices=ACTIVIDADES_EXP_ESTILO_CHOICES, blank=True, null=True)
    fecha_solicitud_exp = models.DateField(blank=True, null=True)
    fecha_solicitud_mkt = models.DateField(blank=True, null=True)
    fecha_entrega_mkt = models.DateField(blank=True, null=True)
    comunicado_aviso = models.CharField(max_length=50, choices=ACTIVIDADES_EXP_COMUNICADO_CHOICES, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    estatus_envio = models.BooleanField(default=False)
    fecha_envio = models.DateField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_solicitud_exp", "-creado"]
        verbose_name = "Actividad Exp"
        verbose_name_plural = "Actividades Exp"

    def __str__(self) -> str:
        return self.tarea
