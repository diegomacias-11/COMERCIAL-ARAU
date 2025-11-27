from django.db import models
from django.core.validators import RegexValidator

class Alianza(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", "El teléfono debe tener exactamente 10 dígitos.")],
    )
    correo = models.EmailField("Correo", max_length=150, blank=True, null=True)

    def __str__(self) -> str:
        return self.nombre
