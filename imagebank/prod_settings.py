import os
from imagebank.settings import *
DEBUG = False
ALLOWED_HOSTS = [
    'localhost',
    '*',
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'NAME': os.environ.get('DB_NAME', 'imagebank'),
        'USER': os.environ.get('DB_USER', 'imagebank'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'imagebankpass'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}

STATIC_ROOT = '/var/www/static'
MEDIA_ROOT = '/var/www/media'
