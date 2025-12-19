from django.db import migrations, models
from datetime import date, timedelta


def _add_business_days(start, days):
    if start is None or days is None:
        return None
    current = start
    remaining = int(days)
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def calcular_estatus(fecha_inicio, dias, fecha_fin):
    compromiso = _add_business_days(fecha_inicio, dias)
    if compromiso is None:
        return ""

    hoy = date.today()
    fin = fecha_fin

    if fin is None:
        if hoy < compromiso:
            return "En tiempo"
        if hoy == compromiso:
            return "Vence hoy"
        if hoy > compromiso:
            return "Se entregó tarde"
    else:
        if fin > compromiso:
            return "Se entregó tarde"
        if fin <= compromiso:
            return "Entregada a tiempo"
    return ""


def set_estatus(apps, schema_editor):
    ActividadMerca = apps.get_model("actividades_merca", "ActividadMerca")
    for act in ActividadMerca.objects.all():
        act.estatus = calcular_estatus(act.fecha_inicio, act.dias, act.fecha_fin)
        act.save(update_fields=["estatus"])


class Migration(migrations.Migration):

    dependencies = [
        ("actividades_merca", "0002_alter_actividadmerca_area_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="actividadmerca",
            name="estatus",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=50,
                choices=[
                    ("En tiempo", "En tiempo"),
                    ("Vence hoy", "Vence hoy"),
                    ("Se entregó tarde", "Se entregó tarde"),
                    ("Entregada a tiempo", "Entregada a tiempo"),
                ],
            ),
        ),
        migrations.RunPython(set_estatus, migrations.RunPython.noop),
    ]
