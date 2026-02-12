from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production-use-env-var')

DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'

ALLOWED_HOSTS = ['*']  # Pi serves to local network

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'portal',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cdnnode.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'portal.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'cdnnode.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []  # Simplified for local network use

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media (content files) — point MEDIA_ROOT to external drive on Pi
# On Pi: export MEDIA_ROOT=/mnt/usb  before starting the service
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', str(BASE_DIR / 'media')))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CDN Node identity — configure via environment variables on Pi
CDN_NODE_NAME = os.environ.get('CDN_NODE_NAME', 'Community CDN Node')
CDN_NODE_TAGLINE = os.environ.get('CDN_NODE_TAGLINE', 'Your local content delivery network')
CDN_PLATFORM_URL = os.environ.get('CDN_PLATFORM_URL', '')
CDN_API_KEY = os.environ.get('CDN_API_KEY', '')
CDN_NODE_IDENTIFIER = os.environ.get('CDN_NODE_IDENTIFIER', '')
CDN_HEARTBEAT_INTERVAL = int(os.environ.get('CDN_HEARTBEAT_INTERVAL', '60'))

# Large file uploads
DATA_UPLOAD_MAX_MEMORY_SIZE = 4 * 1024 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 4 * 1024 * 1024 * 1024
