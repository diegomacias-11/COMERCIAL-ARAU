from django.db import models
from django.core.validators import RegexValidator


class Cliente(models.Model):
    cliente = models.CharField(max_length=150)
    giro = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=50, blank=True, null=True)
    contacto = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", "El teléfono debe tener exactamente 10 dígitos.")],
    )
    conexion = models.CharField(max_length=150, blank=True, null=True)
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
