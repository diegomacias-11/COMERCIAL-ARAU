from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Cliente


def _sync_experiencia(cliente: Cliente):
    try:
        from experiencia.models import ExperienciaCliente
    except Exception:
        return

    ExperienciaCliente.objects.update_or_create(
        cliente_id=cliente.id,
        defaults={
            "cliente": cliente.cliente,
            "servicio": cliente.servicio,
            "giro": cliente.giro,
            "contacto": cliente.contacto,
            "telefono": cliente.telefono,
            "correo": cliente.correo,
            "activo": cliente.activo,
        },
    )


@receiver(post_save, sender=Cliente)
def cliente_post_save(sender, instance: Cliente, created, **kwargs):
    _sync_experiencia(instance)


@receiver(post_delete, sender=Cliente)
def cliente_post_delete(sender, instance: Cliente, **kwargs):
    try:
        from experiencia.models import ExperienciaCliente
    except Exception:
        return
    ExperienciaCliente.objects.filter(cliente_id=instance.id).delete()
