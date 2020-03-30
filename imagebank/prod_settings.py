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

DEFAULT_FILE_STORAGE = os.environ.get(
    'DEFAULT_FILE_STORAGE',
    'django.core.files.storage.FileSystemStorage')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_ACL = os.environ.get('AWS_DEFAULT_ACL', 'public-read')
AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN')

STATIC_ROOT = '/var/www/static'
MEDIA_ROOT = '/var/www/media'
