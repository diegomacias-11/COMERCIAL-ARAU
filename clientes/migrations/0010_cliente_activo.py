from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0009_alter_cliente_medio"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="activo",
            field=models.BooleanField(default=True),
        ),
    ]
