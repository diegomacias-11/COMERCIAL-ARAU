from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0002_venta_fecha_arranque_venta_fecha_pago_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="venta",
            name="facturadora",
            field=models.CharField(
                blank=True,
                choices=[("Anmara", "Anmara"), ("Morwell", "Morwell")],
                max_length=100,
                null=True,
            ),
        ),
    ]
