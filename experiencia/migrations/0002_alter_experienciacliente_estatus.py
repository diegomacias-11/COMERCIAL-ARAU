from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiencia", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="experienciacliente",
            name="activo",
        ),
        migrations.AddField(
            model_name="experienciacliente",
            name="estatus_cliente",
            field=models.CharField(
                choices=[
                    ("Activo", "Activo"),
                    ("Baja", "Baja"),
                    ("Pausa", "Pausa"),
                    ("Reingreso", "Reingreso"),
                ],
                default="Activo",
                max_length=20,
            ),
        ),
    ]
