#!/bin/sh
set -e
DATABASE_URL='' python manage.py collectstatic --noinput

if [ "x$DJANGO_MANAGEPY_MIGRATE" = 'xon' ]; then
  ./wait-for-it.sh $DB_HOST:$DB_PORT -t 30
  python manage.py migrate --noinput
fi

if [ "x$DJANGO_MANAGEPY_INITADMIN" = 'xon' ]; then
  python manage.py initadmin
fi

exec uwsgi imagebank/uwsgi.ini