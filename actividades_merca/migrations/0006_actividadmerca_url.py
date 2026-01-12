from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actividades_merca", "0005_alter_actividadmerca_mercadologo"),
    ]

    operations = [
        migrations.AddField(
            model_name="actividadmerca",
            name="url",
            field=models.URLField(blank=True, null=True),
        ),
    ]
