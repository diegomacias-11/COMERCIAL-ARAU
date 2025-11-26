from django.db import models
from django.core.validators import RegexValidator


# Catálogos de opciones
TIPO_CHOICES = [
    ("Producto", "Producto"),
    ("Servicio", "Servicio"),
]

MEDIO_CHOICES = [
    ("Apollo", "Apollo"),
    ("Remarketing", "Remarketing"),
    ("Alianzas", "Alianzas"),
    ("Lead", "Lead"),
    ("Procompite", "Procompite"),
    ("Ejecutivos", "Ejecutivos"),
    ("Personales", "Personales"),
    ("Expos / Eventos Deportivos", "Expos / Eventos Deportivos"),
]

SERVICIO_CHOICES = [
    ("Pendiente", "Pendiente"),
    ("Auditoría Contable", "Auditoría Contable"),
    ("Contabilidad", "Contabilidad"),
    ("Corridas", "Corridas"),
    ("E-Commerce", "E-Commerce"),
    ("Laboral", "Laboral"),
    ("Maquila de Nómina", "Maquila de Nómina"),
    ("Marketing", "Marketing"),
    ("Reclutamiento", "Reclutamiento"),
    ("REPSE", "REPSE"),
]

VENDEDOR_CHOICES = [
    ("Giovanni", "Giovanni"),
    ("Daniel S.", "Daniel S."),
]

ESTATUS_CITA_CHOICES = [
    ("Agendada", "Agendada"),
    ("Pospuesta", "Pospuesta"),
    ("Cancelada", "Cancelada"),
    ("Atendida", "Atendida"),
]

ESTATUS_SEGUIMIENTO_CHOICES = [
    ("Esperando respuesta del cliente", "Esperando respuesta del cliente"),
    ("Agendar nueva cita", "Agendar nueva cita"),
    ("Solicitud de propuesta", "Solicitud de propuesta"),
    ("Elaboración de propuesta", "Elaboración de propuesta"),
    ("Propuesta enviada", "Propuesta enviada"),
    ("Se envió auditoría Laboral", "Se envió auditoría Laboral"),
    ("Stand by", "Stand by"),
    ("Pendiente de cierre", "Pendiente de cierre"),
    ("En activación", "En activación"),
    ("Reclutando", "Reclutando"),
    ("Cerrado", "Cerrado"),
    ("No está interesado en este servicio", "No está interesado en este servicio"),
    ("Fuera de su presupuesto", "Fuera de su presupuesto"),
]

LUGAR_CHOICES = [
    ("Oficina de Arau", "Oficina de Arau"),
    ("Oficina del cliente", "Oficina del cliente"),
    ("Zoom", "Zoom"),
]


class Cita(models.Model):
    prospecto = models.CharField(max_length=150)
    giro = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, blank=True, null=True)
    medio = models.CharField(max_length=100, choices=MEDIO_CHOICES)
    servicio = models.CharField(max_length=100, choices=SERVICIO_CHOICES)
    servicio2 = models.CharField(max_length=100, choices=SERVICIO_CHOICES, blank=True, null=True)
    servicio3 = models.CharField(max_length=100, choices=SERVICIO_CHOICES, blank=True, null=True)
    contacto = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", "El teléfono debe tener exactamente 10 dígitos.")],
    )
    conexion = models.CharField(max_length=150, blank=True, null=True)
    vendedor = models.CharField(max_length=50, choices=VENDEDOR_CHOICES)
    estatus_cita = models.CharField(max_length=50, choices=ESTATUS_CITA_CHOICES, blank=True, null=True)
    numero_cita = models.CharField(max_length=10, choices=[(str(i), str(i)) for i in range(1, 6)], blank=True, null=True)
    estatus_seguimiento = models.CharField(max_length=100, choices=ESTATUS_SEGUIMIENTO_CHOICES, blank=True, null=True)
    comentarios = models.TextField(blank=True, null=True)
    lugar = models.CharField(max_length=50, choices=LUGAR_CHOICES, blank=True, null=True)
    fecha_cita = models.DateTimeField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Aplica formato automático a campos de texto."""
        if self.prospecto:
            self.prospecto = self.prospecto.upper()
        if self.giro:
            self.giro = self.giro.capitalize()
        if self.contacto:
            self.contacto = self.contacto.title()
        if self.conexion:
            self.conexion = self.conexion.title()
        if self.comentarios:
            self.comentarios = self.comentarios.capitalize()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.prospecto} - {self.fecha_cita.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ["-fecha_cita"]
        verbose_name = "Cita"
        verbose_name_plural = "Citas"

