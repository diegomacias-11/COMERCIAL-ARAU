from django.db import migrations


def sync_estatus_forward(apps, schema_editor):
    # No-op: estatus syncing removed
    return


def sync_estatus_backward(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("experiencia", "0002_alter_experienciacliente_estatus"),
        ("clientes", "0010_cliente_estatus_cliente"),
    ]

    operations = [
        migrations.RunPython(sync_estatus_forward, reverse_code=sync_estatus_backward),
    ]
