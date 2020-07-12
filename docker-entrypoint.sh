#!/bin/sh
PYTHON="${PYTHON:-python}"
set -e
DATABASE_URL='' $PYTHON manage.py collectstatic --noinput

if [ "x$DJANGO_MANAGEPY_MIGRATE" = 'xon' ]; then
  if [ "x$DB_HOST" != "x" ] && [ "x$DB_PORT" != "x" ]; then
    ./wait-for-it.sh $DB_HOST:$DB_PORT -t 30
  fi
  $PYTHON manage.py migrate --noinput
fi

if [ "x$DJANGO_MANAGEPY_INITADMIN" = 'xon' ]; then
  $PYTHON manage.py initadmin
fi

#exec uwsgi imagebank/uwsgi.ini
python manage.py runserver 0.0.0.0:8000