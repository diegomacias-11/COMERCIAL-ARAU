from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

"""
Autoregistra todos los modelos instalados para que respeten los permisos
configurados en el admin sin tener que declararlos manualmente.
"""

for model in apps.get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
