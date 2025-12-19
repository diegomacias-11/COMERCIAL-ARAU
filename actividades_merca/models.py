from datetime import date, timedelta

from django.db import models

from core.choices import (
    AREA_CHOICES,
    MERCADOLOGO_CHOICES,
    DISEÑADOR_CHOICES,
    EVALUACION_CHOICES,
)


def _add_business_days(start: date, days: int | None) -> date | None:
    """Suma días hábiles (excluye fines de semana)."""
    if start is None or days is None:
        return None
    current = start
    remaining = int(days)
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


class ActividadMerca(models.Model):
    cliente = models.CharField(max_length=200)
    area = models.CharField(max_length=100, choices=AREA_CHOICES)
    fecha_inicio = models.DateField()
    tarea = models.CharField(max_length=255)
    dias = models.PositiveIntegerField(default=0)
    mercadologo = models.CharField(max_length=100, choices=MERCADOLOGO_CHOICES, blank=True, null=True)
    disenador = models.CharField(max_length=100, choices=DISEÑADOR_CHOICES, blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    evaluacion = models.CharField(max_length=50, choices=EVALUACION_CHOICES, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_inicio", "-fecha_registro"]
        verbose_name = "Actividad de Marketing"
        verbose_name_plural = "Actividades de Marketing"

    def __str__(self):
        return f"{self.cliente} - {self.tarea}"

    @property
    def fecha_compromiso(self) -> date | None:
        return _add_business_days(self.fecha_inicio, self.dias)

    @property
    def estatus(self) -> str:
        """
        Lógica:
        - Sin fecha fin:
            hoy < compromiso: En tiempo
            hoy = compromiso: Vence hoy
            hoy > compromiso: Se entregó tarde
        - Con fecha fin:
            fin > compromiso: Se entregó tarde
            fin <= compromiso: Entregada a tiempo
        """
        compromiso = self.fecha_compromiso
        if compromiso is None:
            return ""

        hoy = date.today()
        fin = self.fecha_fin

        if fin is None:
            if hoy < compromiso:
                return "En tiempo"
            if hoy == compromiso:
                return "Vence hoy"
            if hoy > compromiso:
                return "Se entregó tarde"
        else:
            if fin > compromiso:
                return "Se entregó tarde"
            if fin <= compromiso:
                return "Entregada a tiempo"
        return ""
