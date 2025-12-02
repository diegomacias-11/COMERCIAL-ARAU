from django.apps import AppConfig


class ComisionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comisiones'

    def ready(self):
        from . import signals  # noqa: F401
