from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ActividadMerca",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cliente", models.CharField(max_length=200)),
                ("area", models.CharField(choices=[('AnÇ·lisis de Mkt', 'AnÇ·lisis de Mkt'), ('Branding', 'Branding'), ('Parrilla', 'Parrilla'), ('VÇ·deos', 'VÇ·deos'), ('CampaÇñas', 'CampaÇñas'), ('PÇ·gina Web DiseÇ·o/Mtto', 'PÇ·gina Web DiseÇ·o/Mtto'), ('Blog', 'Blog'), ('Reportes', 'Reportes'), ('ComercializaciÇ·n', 'ComercializaciÇ·n'), ('Internas', 'Internas'), ('CapacitaciÇ·n y/o juntas', 'CapacitaciÇ·n y/o juntas'), ('Extras', 'Extras'), ('Performance Mkt', 'Performance Mkt')], max_length=100)),
                ("fecha_inicio", models.DateField()),
                ("tarea", models.CharField(max_length=255)),
                ("dias", models.PositiveIntegerField(default=0)),
                ("mercadologo", models.CharField(choices=[('Todos', 'Todos'), ('Paty L.', 'Paty L.')], max_length=100)),
                ("disenador", models.CharField(choices=[('Todos', 'Todos'), ('Leo G.', 'Leo G.'), ('Luis F.', 'Luis F.'), ('Sabine G.', 'Sabine G.')], max_length=100)),
                ("fecha_fin", models.DateField(blank=True, null=True)),
                ("evaluacion", models.CharField(blank=True, choices=[('Excelente', 'Excelente'), ('Muy Bueno', 'Muy Bueno'), ('Regular', 'Regular'), ('Malo', 'Malo')], max_length=50, null=True)),
                ("fecha_registro", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-fecha_inicio", "-fecha_registro"],
                "verbose_name": "Actividad de Marketing",
                "verbose_name_plural": "Actividades de Marketing",
            },
        ),
    ]
