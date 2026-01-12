from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comercial", "0012_alter_cita_medio"),
    ]

    operations = [
        migrations.AddField(
            model_name="cita",
            name="puesto",
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name="cita",
            name="domicilio",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="cita",
            name="pagina_web",
            field=models.URLField(blank=True, null=True, verbose_name="Página web"),
        ),
        migrations.AddField(
            model_name="cita",
            name="linkedin",
            field=models.URLField(blank=True, null=True, verbose_name="LinkedIn"),
        ),
        migrations.AddField(
            model_name="cita",
            name="otra_red",
            field=models.URLField(blank=True, null=True, verbose_name="Otra red"),
        ),
    ]
