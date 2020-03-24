#!/bin/sh
set -e
python manage.py collectstatic --noinput
./wait-for-it.sh $DB_HOST:$DB_PORT
if [ "x$DJANGO_MANAGEPY_MIGRATE" = 'xon' ]; then
    python manage.py migrate --noinput
fi
exec uwsgi imagebank/uwsgi.ini