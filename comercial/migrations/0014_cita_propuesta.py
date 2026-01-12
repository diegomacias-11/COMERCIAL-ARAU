from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comercial", "0013_cita_campos_contacto"),
    ]

    operations = [
        migrations.AddField(
            model_name="cita",
            name="propuesta",
            field=models.URLField(blank=True, null=True, verbose_name="Propuesta"),
        ),
    ]
