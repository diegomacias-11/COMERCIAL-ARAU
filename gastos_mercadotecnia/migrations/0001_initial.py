from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GastoMercadotecnia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_facturacion", models.DateField(blank=True, null=True)),
                ("categoria", models.CharField(blank=True, choices=[("Pautas", "Pautas"), ("Licencias", "Licencias"), ("Hosting", "Hosting"), ("Dominio", "Dominio"), ("Mail", "Mail")], max_length=50, null=True)),
                ("plataforma", models.CharField(blank=True, choices=[("LinkedIn", "LinkedIn"), ("Meta", "Meta"), ("Adobe", "Adobe"), ("CapCut", "CapCut"), ("Google", "Google"), ("Wix", "Wix"), ("Outlook", "Outlook"), ("Gmail", "Gmail"), ("ChatGpt", "ChatGpt")], max_length=50, null=True)),
                ("marca", models.CharField(blank=True, choices=[("ENROK", "ENROK"), ("HunterLoop", "HunterLoop"), ("Capheues", "Capheues"), ("ARAU", "ARAU")], max_length=50, null=True)),
                ("tdc", models.CharField(blank=True, choices=[("8309", "8309"), ("4002", "4002"), ("1002", "1002")], max_length=20, null=True)),
                ("tipo_facturacion", models.CharField(blank=True, choices=[("Fija", "Fija"), ("Variable", "Variable")], max_length=20, null=True)),
                ("periodicidad", models.CharField(blank=True, choices=[("Mensual", "Mensual"), ("C/3 Días", "C/3 Días"), ("Anual", "Anual"), ("Por Campaña", "Por Campaña"), ("C/2mil", "C/2mil"), ("C/5mil", "C/5mil")], max_length=30, null=True)),
                ("facturacion", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("notas", models.TextField(blank=True, null=True)),
                ("creado", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Gasto de Mercadotecnia",
                "verbose_name_plural": "Gastos de Mercadotecnia",
                "ordering": ["-fecha_facturacion", "-creado"],
            },
        ),
    ]
