from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExperienciaCliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cliente_id", models.IntegerField(unique=True)),
                ("cliente", models.CharField(max_length=150)),
                ("servicio", models.CharField(blank=True, max_length=100, null=True)),
                ("giro", models.CharField(blank=True, max_length=150, null=True)),
                ("contacto", models.CharField(blank=True, max_length=150, null=True)),
                ("telefono", models.CharField(blank=True, max_length=20, null=True)),
                ("correo", models.EmailField(blank=True, max_length=254, null=True)),
                ("activo", models.BooleanField(default=True)),
                ("nombre_comercial", models.CharField(blank=True, max_length=200, null=True)),
                ("domicilio", models.CharField(blank=True, max_length=255, null=True)),
                ("puesto", models.CharField(blank=True, max_length=150, null=True)),
                ("fecha_contrato", models.DateField(blank=True, null=True)),
                (
                    "periodicidad",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("1 mes", "1 mes"),
                            ("3 meses", "3 meses"),
                            ("6 meses", "6 meses"),
                            ("1 año", "1 año"),
                            ("2 años", "2 años"),
                            ("proyecto", "Proyecto"),
                            ("semanal", "Semanal"),
                            ("quincenal", "Quincenal"),
                            ("indefinido", "Indefinido"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "chat_welcome",
                    models.CharField(
                        blank=True, choices=[("si", "Sí"), ("no", "No"), ("proceso", "Proceso")], max_length=10, null=True
                    ),
                ),
                ("meet", models.BooleanField(default=False)),
                ("comentarios", models.TextField(blank=True, null=True)),
                ("fecha_registro", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Cliente Experiencia",
                "verbose_name_plural": "Clientes Experiencia",
                "ordering": ["-fecha_registro"],
            },
        ),
    ]
