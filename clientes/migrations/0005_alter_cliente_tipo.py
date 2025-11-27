from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0004_cliente_comisionistas"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cliente",
            name="tipo",
            field=models.CharField(
                blank=True,
                choices=[("Producto", "Producto"), ("Servicio", "Servicio")],
                max_length=50,
                null=True,
            ),
        ),
    ]
