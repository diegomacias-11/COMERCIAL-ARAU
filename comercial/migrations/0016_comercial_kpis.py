from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("comercial", "0015_alter_cita_lugar"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComercialKpi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=150, unique=True)),
                ("descripcion", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "verbose_name": "KPI comercial",
                "verbose_name_plural": "KPIs comerciales",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="ComercialKpiMeta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anio", models.PositiveIntegerField()),
                ("mes", models.PositiveSmallIntegerField(choices=[(1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"), (5, "Mayo"), (6, "Junio"), (7, "Julio"), (8, "Agosto"), (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre")])),
                ("meta", models.DecimalField(decimal_places=2, max_digits=12)),
                ("kpi", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="metas", to="comercial.comercialkpi")),
            ],
            options={
                "verbose_name": "Meta KPI comercial",
                "verbose_name_plural": "Metas KPI comercial",
                "ordering": ["-anio", "-mes", "kpi__nombre"],
                "unique_together": {("kpi", "anio", "mes")},
            },
        ),
    ]
