from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Cita


@receiver(post_save, sender=Cita)
def crear_cliente_al_cerrar(sender, instance: Cita, created: bool, **kwargs):
    """
    Cuando una Cita cambia su estatus_seguimiento a "Cerrado",
    crear/actualizar un registro en la app de clientes y su directorio.
    La fecha de registro se maneja con auto_now_add en el modelo Cliente.
    """
    try:
        from clientes.models import Cliente, Contacto  # import diferido para evitar dependencias circulares en migraciones
    except Exception:
        return

    if instance.estatus_seguimiento == "Cerrado":
        defaults = {
            "giro": instance.giro,
            "tipo": instance.tipo,
            "medio": instance.medio,
            "conexion": instance.conexion,
            "domicilio": instance.domicilio,
            "pagina_web": instance.pagina_web,
            "linkedin": instance.linkedin,
            "otra_red": instance.otra_red,
            "servicio": instance.servicio,
        }
        # Usa update_or_create para evitar duplicados si la Cita se edita muchas veces
        cliente, _ = Cliente.objects.update_or_create(
            cliente=instance.prospecto,
            servicio=instance.servicio,
            defaults=defaults,
        )

        contacto_data = [
            instance.contacto,
            instance.telefono,
            instance.correo,
            instance.puesto,
        ]
        if any(contacto_data):
            if instance.contacto:
                Contacto.objects.update_or_create(
                    cliente=cliente,
                    nombre=instance.contacto,
                    defaults={
                        "telefono": instance.telefono,
                        "correo": instance.correo,
                        "puesto": instance.puesto,
                    },
                )
            elif instance.correo:
                Contacto.objects.update_or_create(
                    cliente=cliente,
                    correo=instance.correo,
                    defaults={
                        "nombre": instance.contacto,
                        "telefono": instance.telefono,
                        "puesto": instance.puesto,
                    },
                )
            else:
                Contacto.objects.create(
                    cliente=cliente,
                    nombre=instance.contacto,
                    telefono=instance.telefono,
                    correo=instance.correo,
                    puesto=instance.puesto,
                )
