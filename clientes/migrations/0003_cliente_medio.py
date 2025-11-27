from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0002_cliente_correo"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="medio",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Medio"),
        ),
    ]
