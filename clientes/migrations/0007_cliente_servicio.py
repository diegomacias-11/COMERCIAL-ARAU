from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0006_alter_cliente_medio"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="servicio",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Pendiente", "Pendiente"),
                    ("Auditoría Contable", "Auditoría Contable"),
                    ("Contabilidad", "Contabilidad"),
                    ("Corridas", "Corridas"),
                    ("E-Commerce", "E-Commerce"),
                    ("Laboral", "Laboral"),
                    ("Maquila de Nómina", "Maquila de Nómina"),
                    ("Marketing", "Marketing"),
                    ("Reclutamiento", "Reclutamiento"),
                    ("REPSE", "REPSE"),
                ],
                max_length=100,
                null=True,
            ),
        ),
    ]
