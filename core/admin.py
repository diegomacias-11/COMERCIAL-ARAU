from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session

"""
Autoregistra todos los modelos instalados para que respeten los permisos
configurados en el admin sin tener que declararlos manualmente.
Si un modelo ya está registrado (por un ModelAdmin personalizado), se omite.
"""

# Saltar modelos que no queremos mostrar
_SKIP_MODELS = {ContentType, Session}

for model in apps.get_models():
    if model in _SKIP_MODELS:
        continue
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
