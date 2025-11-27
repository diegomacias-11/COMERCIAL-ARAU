from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Alianza",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=150)),
                (
                    "telefono",
                    models.CharField(
                        blank=True,
                        max_length=10,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\d{10}$", "El tel\u1ef9fono debe tener exactamente 10 d\ufffdd\ufffdgitos."
                            )
                        ],
                    ),
                ),
                ("correo", models.EmailField(blank=True, max_length=150, null=True, verbose_name="Correo")),
            ],
        ),
    ]
