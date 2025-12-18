from decimal import Decimal, InvalidOperation

from django.db import models
from django.utils import timezone


class Venta(models.Model):

    class EstatusPago(models.TextChoices):
        PENDIENTE = "Pendiente", "Pendiente"
        PAGADO = "Pagado", "Pagado"

    fecha = models.DateField(default=timezone.localdate)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    servicio = models.CharField(max_length=50)
    facturadora = models.CharField(max_length=100, blank=True, null=True)
    num_factura = models.CharField(max_length=100, blank=True, null=True)
    monto_venta = models.DecimalField(max_digits=12, decimal_places=2)
    comision_porcentaje = models.DecimalField(max_digits=7, decimal_places=4, editable=False)
    monto_comision = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    comentarios = models.CharField(max_length=255, blank=True, null=True)
    estatus_pago = models.CharField(max_length=20, choices=EstatusPago.choices, default=EstatusPago.PENDIENTE)

    def __str__(self):
        return f"{self.cliente} - {self.facturadora} - {self.fecha}"

    def save(self, *args, **kwargs):
        rate = None
        # Preferir el total de comisiones definido en Cliente (suma de comisionistas)
        try:
            total_cliente = getattr(self.cliente, "total_comisiones", None)
            if total_cliente is not None:
                rate = Decimal(str(total_cliente))
        except (InvalidOperation, TypeError):
            rate = None

        # Fallback a campos legacy si existen
        if rate in (None, Decimal("0")):
            try:
                if getattr(self.cliente, "comision_servicio", None) is not None:
                    rate = Decimal(str(self.cliente.comision_servicio))
                elif getattr(self.cliente, "comision_procom", None) is not None:
                    rate = Decimal(str(self.cliente.comision_procom))
            except (InvalidOperation, TypeError):
                rate = None

        if rate is None:
            rate_fraction = Decimal("0")
            rate_percent = Decimal("0")
        else:
            rate_fraction = rate if rate <= 1 else (rate / Decimal("100"))
            rate_percent = rate * Decimal("100") if rate <= 1 else rate

        try:
            self.servicio = self.cliente.get_servicio_display()
        except Exception:
            try:
                self.servicio = str(self.cliente.servicio)
            except Exception:
                pass

        if self.monto_venta is None:
            self.monto_venta = Decimal("0")
        self.comision_porcentaje = rate_percent.quantize(Decimal("0.0001"))
        self.monto_comision = (rate_fraction * self.monto_venta).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
