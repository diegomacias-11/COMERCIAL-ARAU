"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Crear superusuario automáticamente si se solicita (solo en Render)
import os
if os.environ.get("CREATE_SUPERUSER") == "1":
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if username and password and not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print("✔ Superusuario creado automáticamente.")
        else:
            print("ℹ El superusuario ya existe o faltan datos.")
    except Exception as e:
        print(f"⚠ Error creando superusuario: {e}")

