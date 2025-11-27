from django.db import models
from django.core.validators import RegexValidator


class Cliente(models.Model):
    cliente = models.CharField(max_length=150)
    giro = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=50, blank=True, null=True)
    medio = models.CharField("Medio", max_length=100, blank=True, null=True)
    contacto = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", "El teléfono debe tener exactamente 10 dígitos.")],
    )
    correo = models.EmailField("Correo", blank=True, null=True)
    conexion = models.CharField(max_length=150, blank=True, null=True)
    comisionista_1 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com1", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_2 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com2", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_3 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com3", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_4 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com4", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_5 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com5", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_6 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com6", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_7 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com7", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_8 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com8", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_9 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com9", on_delete=models.SET_NULL, blank=True, null=True)
    comisionista_10 = models.ForeignKey("alianzas.Alianza", related_name="clientes_com10", on_delete=models.SET_NULL, blank=True, null=True)
    comision_1 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_2 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_3 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_4 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_5 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_6 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_7 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_8 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_9 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    comision_10 = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Formato similar al usado en comercial.Cita
        if self.cliente:
            self.cliente = self.cliente.upper()
        if self.giro:
            self.giro = self.giro.capitalize()
        if self.contacto:
            self.contacto = self.contacto.title()
        if self.conexion:
            self.conexion = self.conexion.title()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.cliente

    class Meta:
        ordering = ["-fecha_registro"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
