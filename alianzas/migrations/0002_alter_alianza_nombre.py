from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alianzas", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alianza",
            name="nombre",
            field=models.CharField(max_length=150, unique=True),
        ),
    ]
