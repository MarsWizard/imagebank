FROM python:3.7-slim
ARG APP_USER=appuser
RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER}
ENV PYTHONUNBUFFERED 1
RUN set -ex \
    && RUN_DEPS=" \
    libpcre3 \
    gcc \
    mime-support \
    default-libmysqlclient-dev \
    python3-dev \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
RUN pip install uwsgi
COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
ADD . /app/
EXPOSE 8000
ENV DJANGO_SETTINGS_MODULE=imagebank.prod_settings
RUN DATABASE_URL='' python manage.py collectstatic --noinput
#ENV UWSGI_WSGI_FILE=imagebank/wsgi.py
#ENV UWSGI_HTTP=:8000 UWSGI_MASTER=1 UWSGI_HTTP_AUTO_CHUNKED=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy
#ENV UWSGI_STATIC_MAP="/static/=/code/static/;/images/=/var/www/media/" UWSGI_STATIC_EXPIRES_URI="/static/.*\.[a-f0-9]{12,}\.(css|js|png|jpg|jpeg|gif|ico|woff|ttf|otf|svg|scss|map|txt) 315360000"
#USER ${APP_USER}:${APP_USER}
CMD ["uwsgi", "imagebank/uwsgi.ini"]
#CMD ["uwsgi", "--show-config"]
#ENTRYPOINT ["/app/docker-entrypoint.sh"]