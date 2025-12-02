from django.db import models
from django.utils import timezone
from decimal import Decimal


class Comision(models.Model):
    venta = models.ForeignKey("ventas.Venta", on_delete=models.CASCADE, related_name="comisiones")
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    comisionista = models.ForeignKey("alianzas.Alianza", on_delete=models.SET_NULL, null=True, blank=True)
    servicio = models.CharField(max_length=50)
    porcentaje = models.DecimalField(max_digits=9, decimal_places=6)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    periodo_mes = models.IntegerField()
    periodo_anio = models.IntegerField()
    liberable_desde = models.DateField()
    liberada = models.BooleanField(default=False)
    estatus_pago_dispersion = models.CharField(max_length=50)
    fecha_dispersion = models.DateField()
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.comisionista} {self.periodo_mes:02d}/{self.periodo_anio} -> {self.monto}"


class PagoComision(models.Model):
    comisionista = models.ForeignKey("alianzas.Alianza", on_delete=models.CASCADE, related_name="pagos_comision")
    periodo_mes = models.IntegerField()
    periodo_anio = models.IntegerField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateField(default=timezone.localdate)
    comentario = models.CharField(max_length=255, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.comisionista} {self.periodo_mes:02d}/{self.periodo_anio}: {self.monto}"

# Create your models here.
