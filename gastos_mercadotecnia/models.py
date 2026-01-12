from django.db import models

from core.choices import (
    GASTOS_MERCA_CATEGORIA_CHOICES,
    GASTOS_MERCA_PLATAFORMA_CHOICES,
    GASTOS_MERCA_MARCA_CHOICES,
    GASTOS_MERCA_TDC_CHOICES,
    GASTOS_MERCA_TIPO_FACTURACION_CHOICES,
    GASTOS_MERCA_PERIODICIDAD_CHOICES,
)


class GastoMercadotecnia(models.Model):
    fecha_facturacion = models.DateField(blank=True, null=True)
    categoria = models.CharField(max_length=50, choices=GASTOS_MERCA_CATEGORIA_CHOICES, blank=True, null=True)
    plataforma = models.CharField(max_length=50, choices=GASTOS_MERCA_PLATAFORMA_CHOICES, blank=True, null=True)
    marca = models.CharField(max_length=50, choices=GASTOS_MERCA_MARCA_CHOICES, blank=True, null=True)
    tdc = models.CharField(max_length=20, choices=GASTOS_MERCA_TDC_CHOICES, blank=True, null=True)
    tipo_facturacion = models.CharField(
        max_length=20, choices=GASTOS_MERCA_TIPO_FACTURACION_CHOICES, blank=True, null=True
    )
    periodicidad = models.CharField(
        max_length=30, choices=GASTOS_MERCA_PERIODICIDAD_CHOICES, blank=True, null=True
    )
    facturacion = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_facturacion", "-creado"]
        verbose_name = "Gasto de Mercadotecnia"
        verbose_name_plural = "Gastos de Mercadotecnia"

    def __str__(self) -> str:
        return f"{self.marca or 'Gasto'} - {self.fecha_facturacion or ''}"
