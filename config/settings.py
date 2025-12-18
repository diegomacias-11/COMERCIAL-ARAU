"""
Django settings for config project.

Configurado para funcionar automáticamente:
- 💻 En local: DEBUG=True (sin variables de entorno)
- ☁️ En Render: DEBUG y demás valores tomados de variables de entorno
"""

from pathlib import Path
import os
import dj_database_url

# ======================
# RUTAS BASE
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent


# ======================
# SEGURIDAD
# ======================
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')  # valor local por defecto
DEBUG = os.environ.get('DEBUG', 'FALSE').lower() == 'true'

# Si no hay variable DEBUG (caso local), forzar modo debug
if not os.environ.get('DEBUG'):
    DEBUG = True

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1 localhost').split()


# ======================
# APLICACIONES
# ======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'clientes',
    'comercial',
    'alianzas',
    'ventas',
    'comisiones',
    'leads',
    'actividades_merca',
]


# ======================"""  """
# MIDDLEWARE
# ======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise para servir estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.LoginRequiredMiddleware',
    'core.middleware.GroupPermissionMiddleware',
]


# ======================
# URLS / TEMPLATES / WSGI
# ======================
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ======================
# BASE DE DATOS
# ======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Si existe DATABASE_URL (Render), usarla
database_url = os.environ.get('DATABASE_URL')
if database_url:
    DATABASES['default'] = dj_database_url.parse(database_url)


# ======================
# VALIDACIÓN DE CONTRASEÑAS
# ======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ======================
# INTERNACIONALIZACIÓN
# ======================
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True


# ======================
# ARCHIVOS ESTÁTICOS
# ======================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ======================
# CLAVE PRIMARIA POR DEFECTO
# ======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/citas/'
# Mensaje de error simplificado
from django.contrib.messages import constants as messages  # noqa
MESSAGE_TAGS = {
    messages.ERROR: 'error',
}
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_SAVE_EVERY_REQUEST = True  # renovar inactividad en cada request
