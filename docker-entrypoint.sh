#!/bin/sh
set -e
python manage.py collectstatic
if [ "x$DJANGO_MANAGEPY_MIGRATE" = 'xon' ]; then
    python manage.py migrate --noinput
fi
exec uwsgi imagebank/uwsgi.ini