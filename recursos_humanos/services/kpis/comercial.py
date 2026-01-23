from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from comercial.models import Cita


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def kpi_citas_comerciales(mes: int, anio: int) -> int:
    """Cuenta primeras citas atendidas en el mes/anio indicado."""
    if not mes or not anio:
        return 0
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime(anio, mes, 1, 0, 0, 0), tz)
    if mes == 12:
        end = timezone.make_aware(datetime(anio + 1, 1, 1, 0, 0, 0), tz)
    else:
        end = timezone.make_aware(datetime(anio, mes + 1, 1, 0, 0, 0), tz)
    return (
        Cita.objects.filter(
            fecha_cita__gte=start,
            fecha_cita__lt=end,
            numero_cita__iexact="Primera",
            estatus_cita__iexact="Atendida",
        )
        .count()
    )


def resolver_kpi(nombre_kpi: str, mes: int, anio: int) -> int | None:
    """
    Resuelve el KPI por nombre normalizado.
    - "citas comerciales" -> conteo de primeras citas atendidas del mes.
    - "cierres de ventas" -> conteo de citas con estatus seguimiento "Cerrado".
    """
    nombre = _normalize(nombre_kpi)
    if nombre == _normalize("Citas Comerciales"):
        return kpi_citas_comerciales(mes, anio)
    if nombre == _normalize("Cierres de ventas"):
        if not mes or not anio:
            return 0
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime(anio, mes, 1, 0, 0, 0), tz)
        if mes == 12:
            end = timezone.make_aware(datetime(anio + 1, 1, 1, 0, 0, 0), tz)
        else:
            end = timezone.make_aware(datetime(anio, mes + 1, 1, 0, 0, 0), tz)
        return (
            Cita.objects.filter(
                fecha_cita__gte=start,
                fecha_cita__lt=end,
                estatus_seguimiento__iexact="Cerrado",
            )
            .count()
        )
    return None
