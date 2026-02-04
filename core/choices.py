TIPO_CHOICES = [
    ("Producto", "Producto"),
    ("Servicio", "Servicio"),
]

MEDIO_CHOICES = [
    ("Alianzas", "Alianzas"),
    ("Apollo", "Apollo"),
    ("Ejecutivos", "Ejecutivos"),
    ("Expos / Eventos Deportivos", "Expos / Eventos Deportivos"),
    ("Lead", "Lead"),
    ("Personales", "Personales"),
    ("Procompite", "Procompite"),
    ("Remarketing", "Remarketing"),
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
    ("Materialidad", "Materialidad"),
    ("Reclutamiento", "Reclutamiento"),
    ("REPSE", "REPSE"),
]

LEAD_ESTATUS_CHOICES = [
    ("Perdido", "Perdido"),
    ("No calificado", "No calificado"),
    ("Calificado", "Calificado"),
    ("Convertido", "Convertido"),
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

NUM_CITA_CHOICES = [
    ("Primera", "Primera"),
    ("Segunda", "Segunda"),
    ("Tercera", "Tercera"),
    ("Cuarta", "Cuarta"),
    ("Quinta", "Quinta"),
]

ESTATUS_SEGUIMIENTO_CHOICES = [
    ("Esperando respuesta del cliente", "Esperando respuesta del cliente"),
    ("Agendar nueva cita", "Agendar nueva cita"),
    ("Solicitud de propuesta", "Solicitud de propuesta"),
    ("ElaboraciÃ³n de propuesta", "ElaboraciÃ³n de propuesta"),
    ("Propuesta enviada", "Propuesta enviada"),
    ("Se enviÃ³ auditorÃ­a Laboral", "Se enviÃ³ auditorÃ­a Laboral"),
    ("Stand by", "Stand by"),
    ("Pendiente de cierre", "Pendiente de cierre"),
    ("En activaciÃ³n", "En activaciÃ³n"),
    ("Reclutando", "Reclutando"),
    ("Cerrado", "Cerrado"),
    ("No estÃ¡ interesado en este servicio", "No estÃ¡ interesado en este servicio"),
    ("Fuera de su presupuesto", "Fuera de su presupuesto"),
]

LUGAR_CHOICES = [
    ("Oficina de Arau", "Oficina de Arau"),
    ("Oficina del cliente", "Oficina del cliente"),
    ("Zoom", "Zoom"),
    ("TelÃ©fono", "TelÃ©fono"),
    ("Correo", "Correo"),
]

MES_CHOICES = [
    (1, "Enero"),
    (2, "Febrero"),
    (3, "Marzo"),
    (4, "Abril"),
    (5, "Mayo"),
    (6, "Junio"),
    (7, "Julio"),
    (8, "Agosto"),
    (9, "Septiembre"),
    (10, "Octubre"),
    (11, "Noviembre"),
    (12, "Diciembre"),
]

AREA_CHOICES = [
    ("Análisis de Mkt", "Análisis de Mkt"),
    ("Blog", "Blog"),
    ("Branding", "Branding"),
    ("Campañas", "Campañas"),
    ("Capacitación y/o juntas", "Capacitación y/o juntas"),
    ("Comercialización", "Comercialización"),
    ("Extras", "Extras"),
    ("Internas", "Internas"),
    ("Página Web Diseño/Mtto", "Página Web Diseño/Mtto"),
    ("Parrilla", "Parrilla"),
    ("Performance Mkt", "Performance Mkt"),
    ("Vídeos", "Vídeos"),
]

MERCADOLOGO_CHOICES = [
    ("Aldo S.", "Aldo S."),
    ("Paty L.", "Paty L."),
    ("Todos", "Todos"),
]

DISEÑADOR_CHOICES = [
    ("Leo G.", "Leo G."),
    ("Luis F.", "Luis F."),
    ("Sabine G.", "Sabine G."),
    ("Todos", "Todos"),
]

EVALUACION_CHOICES = [
    ("Excelente", "Excelente"),
    ("Muy Bueno", "Muy Bueno"),
    ("Regular", "Regular"),
    ("Malo", "Malo"),
]

EXPERIENCIA_PERIODICIDAD_CHOICES = [
    ("1 mes", "1 mes"),
    ("3 meses", "3 meses"),
    ("6 meses", "6 meses"),
    ("1 año", "1 año"),
    ("2 años", "2 años"),
    ("proyecto", "Proyecto"),
    ("semanal", "Semanal"),
    ("quincenal", "Quincenal"),
    ("indefinido", "Indefinido"),
]

CHAT_WELCOME_CHOICES = [
    ("si", "Sí"),
    ("no", "No"),
    ("proceso", "Proceso"),
]

FACTURADORA_CHOICES = [
    ("Anmara", "Anmara"),
    ("Morwell", "Morwell"),
]

ESTATUS_CLIENTES_CHOICES = [
    ("Activo", "Activo"),
    ("Pausa", "Pausa"),
    ("Baja", "Baja"),
    ("Reingreso", "Reingreso"),
]

ACTIVIDADES_EXP_TIPO_CHOICES = [
    ("Cliente Arau", "Cliente Arau"),
    ("Colaboradores", "Colaboradores"),
]

ACTIVIDADES_EXP_AREA_CHOICES = [
    ("Experiencia", "Experiencia"),
    ("Mercadotecnia", "Mercadotecnia"),
    ("Administración", "Administración"),
    ("Operaciones", "Operaciones"),
    ("Contabilidad", "Contabilidad"),
    ("Comercial", "Comercial"),
    ("Reclutamiento", "Reclutamiento"),
    ("Legal", "Legal"),
    ("Fiscal", "Fiscal"),
    ("Enrok", "Enrok"),
]

ACTIVIDADES_EXP_ESTILO_CHOICES = [
    ("Texto", "Texto"),
    ("Imagen", "Imagen"),
]

ACTIVIDADES_EXP_COMUNICADO_CHOICES = [
    ("Programado", "Programado"),
    ("Especial", "Especial"),
]

GASTOS_MERCA_CATEGORIA_CHOICES = [
    ("Pautas", "Pautas"),
    ("Licencias", "Licencias"),
    ("Hosting", "Hosting"),
    ("Dominio", "Dominio"),
    ("Mail", "Mail"),
]

GASTOS_MERCA_PLATAFORMA_CHOICES = [
    ("LinkedIn", "LinkedIn"),
    ("Meta", "Meta"),
    ("Adobe", "Adobe"),
    ("CapCut", "CapCut"),
    ("Google", "Google"),
    ("Wix", "Wix"),
    ("Outlook", "Outlook"),
    ("Gmail", "Gmail"),
    ("ChatGpt", "ChatGpt"),
]

GASTOS_MERCA_MARCA_CHOICES = [
    ("ENROK", "ENROK"),
    ("HunterLoop", "HunterLoop"),
    ("Capheues", "Capheues"),
    ("ARAU", "ARAU"),
]

GASTOS_MERCA_TDC_CHOICES = [
    ("8309", "8309"),
    ("4002", "4002"),
    ("1002", "1002"),
]

GASTOS_MERCA_TIPO_FACTURACION_CHOICES = [
    ("Fija", "Fija"),
    ("Variable", "Variable"),
]

GASTOS_MERCA_PERIODICIDAD_CHOICES = [
    ("Mensual", "Mensual"),
    ("C/3 Días", "C/3 Días"),
    ("Anual", "Anual"),
    ("Por Campaña", "Por Campaña"),
    ("C/2mil", "C/2mil"),
    ("C/5mil", "C/5mil"),
]

CONTROL_PERIODICIDAD_CHOICES = [
    ('mensual', 'Mensual'),
    ('trimestral', 'Trimestral'),
    ('semestral', 'Semestral'),
    ('anual', 'Anual'),
]
