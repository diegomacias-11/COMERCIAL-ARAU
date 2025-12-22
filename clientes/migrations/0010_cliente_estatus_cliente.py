from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0009_alter_cliente_medio"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE clientes_cliente DROP COLUMN IF EXISTS activo;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
