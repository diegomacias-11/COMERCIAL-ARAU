from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="correo",
            field=models.EmailField("Correo", blank=True, max_length=254, null=True),
        ),
    ]
