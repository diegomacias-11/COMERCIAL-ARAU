from django.db import models
from django.core.validators import RegexValidator
from core.choices import TIPO_CHOICES, MEDIO_CHOICES, SERVICIO_CHOICES


class Cliente(models.Model):
    cliente = models.CharField(max_length=150)
    servicio = models.CharField(max_length=100, choices=SERVICIO_CHOICES, blank=True, null=True)
    giro = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, blank=True, null=True)
    medio = models.CharField("Medio", max_length=100, choices=MEDIO_CHOICES, blank=True, null=True)
    conexion = models.CharField(max_length=150, blank=True, null=True)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    pagina_web = models.URLField("Página web", blank=True, null=True)
    linkedin = models.URLField("LinkedIn", blank=True, null=True)
    otra_red = models.URLField("Otra red", blank=True, null=True)
    propuesta = models.URLField("Propuesta", blank=True, null=True)
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
    total_comisiones = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.cliente:
            self.cliente = self.cliente.upper()
        if self.giro:
            self.giro = self.giro.capitalize()
        if self.conexion:
            self.conexion = self.conexion.title()
        # Recalcula el total de comisiones (suma de los decimales almacenados)
        comisiones = [
            self.comision_1, self.comision_2, self.comision_3, self.comision_4, self.comision_5,
            self.comision_6, self.comision_7, self.comision_8, self.comision_9, self.comision_10,
        ]
        self.total_comisiones = sum([c for c in comisiones if c is not None]) if any(comisiones) else 0
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.cliente

    class Meta:
        ordering = ["-fecha_registro"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Contacto(models.Model):
    cliente = models.ForeignKey(Cliente, related_name="contactos", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", "El teléfono debe tener exactamente 10 dígitos.")],
    )
    correo = models.EmailField("Correo", blank=True, null=True)
    puesto = models.CharField(max_length=150, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.nombre or f"Contacto de {self.cliente}"

    class Meta:
        ordering = ["-fecha_registro"]
        verbose_name = "Contacto"
        verbose_name_plural = "Contactos"
