from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Cita


@receiver(post_save, sender=Cita)
def crear_cliente_al_cerrar(sender, instance: Cita, created: bool, **kwargs):
    """
    Cuando una Cita cambia su estatus_seguimiento a "Cerrado",
    crear/actualizar un registro en la app de clientes con:
    cliente (prospecto), giro, tipo, contacto, telefono, conexion.
    La fecha de registro se maneja con auto_now_add en el modelo Cliente.
    """
    try:
        from clientes.models import Cliente  # import diferido para evitar dependencias circulares en migraciones
    except Exception:
        return

    if instance.estatus_seguimiento == "Cerrado":
        defaults = {
            "giro": instance.giro,
            "tipo": instance.tipo,
            "contacto": instance.contacto,
            "telefono": instance.telefono,
            "conexion": instance.conexion,
        }
        # Usa update_or_create para evitar duplicados si la Cita se edita múltiples veces
        Cliente.objects.update_or_create(
            cliente=instance.prospecto,
            defaults=defaults,
        )

