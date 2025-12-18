from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0007_cliente_servicio"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="total_comisiones",
            field=models.DecimalField(decimal_places=6, default=0, max_digits=10),
        ),
    ]
