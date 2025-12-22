from django.apps import AppConfig


class ClientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clientes'

    def ready(self):
        # Importa señales para sincronizar con experiencia
        from . import signals  # noqa: F401
