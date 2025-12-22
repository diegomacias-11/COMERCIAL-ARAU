from django.db import migrations


def sync_estatus_forward(apps, schema_editor):
    ExperienciaCliente = apps.get_model("experiencia", "ExperienciaCliente")
    Cliente = apps.get_model("clientes", "Cliente")
    for exp in ExperienciaCliente.objects.all():
        Cliente.objects.filter(pk=exp.cliente_id).update(estatus_cliente=exp.estatus_cliente)


def sync_estatus_backward(apps, schema_editor):
    # No-op rollback
    return


class Migration(migrations.Migration):

    dependencies = [
        ("experiencia", "0002_alter_experienciacliente_estatus"),
        ("clientes", "0010_cliente_estatus_cliente"),
    ]

    operations = [
        migrations.RunPython(sync_estatus_forward, reverse_code=sync_estatus_backward),
    ]
