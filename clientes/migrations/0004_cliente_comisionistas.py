from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("alianzas", "0002_alter_alianza_nombre"),
        ("clientes", "0003_cliente_medio"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="comision_1",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_10",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_2",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_3",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_4",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_5",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_6",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_7",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_8",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comision_9",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_1",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com1", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_10",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com10", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_2",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com2", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_3",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com3", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_4",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com4", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_5",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com5", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_6",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com6", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_7",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com7", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_8",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com8", to="alianzas.alianza"),
        ),
        migrations.AddField(
            model_name="cliente",
            name="comisionista_9",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clientes_com9", to="alianzas.alianza"),
        ),
    ]
