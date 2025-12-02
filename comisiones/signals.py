from datetime import date
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from ventas.models import Venta
from .models import Comision


def _first_day_next_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


@receiver(post_save, sender=Venta)
def generar_comisiones(sender, instance: Venta, created, **kwargs):
    Comision.objects.filter(venta=instance).delete()

    cliente = instance.cliente
    periodo_mes = instance.fecha.month
    periodo_anio = instance.fecha.year
    liberable_desde = _first_day_next_month(instance.fecha)

    for i in range(1, 11):
        com_field = f"comisionista_{i}"
        pct_field = f"comision_{i}"
        comisionista = getattr(cliente, com_field, None)
        pct = getattr(cliente, pct_field, None)
        if comisionista and pct is not None and Decimal(pct) > 0:
            monto = (Decimal(pct) * Decimal(instance.monto_venta)).quantize(Decimal("0.01"))
            liberada = str(getattr(instance, "estatus_pago", "")) == "Pagado"
            Comision.objects.create(
                venta=instance,
                cliente=cliente,
                comisionista=comisionista,
                servicio=getattr(instance, "servicio", ""),
                porcentaje=Decimal(pct),
                monto=monto,
                periodo_mes=periodo_mes,
                periodo_anio=periodo_anio,
                liberable_desde=liberable_desde,
                liberada=liberada,
                estatus_pago_dispersion=getattr(instance, "estatus_pago", ""),
                fecha_dispersion=instance.fecha,
            )
