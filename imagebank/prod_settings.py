import os
from imagebank.settings import *


DEBUG = False
ALLOWED_HOSTS = [
    'localhost',
    '*',
]
DATABASES = {
    'default': {

    }
}

db_engine = os.environ.get('DB_ENGINE', 'django.db.backends.mysql')
if db_engine == 'django.db.backends.mysql':
    DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
    DATABASES['default']['HOST'] = os.environ.get('DB_HOST', '127.0.0.1')
    DATABASES['default']['PORT'] = os.environ.get('DB_PORT', '3306')
    DATABASES['default']['NAME'] = os.environ.get('DB_NAME', 'imagebank')
    DATABASES['default']['USER'] = os.environ.get('DB_USER', 'imagebank')
    DATABASES['default']['PASSWORD'] = os.environ.get('DB_PASSWORD', 'imagebankpass')
    DATABASES['default']['OPTIONS'] = {'charset': 'utf8mb4'}

if db_engine == 'django.db.backends.sqlite3':
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
    DATABASES['default']['NAME'] = os.environ.get('DB_NAME', 'db.sqlite3')


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
