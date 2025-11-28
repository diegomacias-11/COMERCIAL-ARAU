from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0005_alter_cliente_tipo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cliente",
            name="medio",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Apollo", "Apollo"),
                    ("Remarketing", "Remarketing"),
                    ("Alianzas", "Alianzas"),
                    ("Lead", "Lead"),
                    ("Procompite", "Procompite"),
                    ("Ejecutivos", "Ejecutivos"),
                    ("Personales", "Personales"),
                    ("Expos / Eventos Deportivos", "Expos / Eventos Deportivos"),
                ],
                max_length=100,
                null=True,
                verbose_name="Medio",
            ),
        ),
    ]
