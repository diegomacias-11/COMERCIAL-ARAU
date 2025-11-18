from django.apps import AppConfig


class ComercialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comercial'

    def ready(self):
        # Importa señales para registrar handlers de post_save
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Evita fallar en importación temprana (migraciones, etc.)
            pass
