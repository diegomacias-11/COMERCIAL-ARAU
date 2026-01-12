from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0012_remove_cliente_contacto_remove_cliente_correo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="domicilio",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="pagina_web",
            field=models.URLField(blank=True, null=True, verbose_name="Página web"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="linkedin",
            field=models.URLField(blank=True, null=True, verbose_name="LinkedIn"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="otra_red",
            field=models.URLField(blank=True, null=True, verbose_name="Otra red"),
        ),
    ]
