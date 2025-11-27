from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comercial", "0010_alter_cita_numero_cita"),
    ]

    operations = [
        migrations.AddField(
            model_name="cita",
            name="correo",
            field=models.EmailField("Correo", blank=True, max_length=254, null=True),
        ),
    ]
