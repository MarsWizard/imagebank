class { 'docker':
  docker_users => ['root'],
}

class {'docker::compose':
  ensure => present,
  version => '1.16.1',
}
#
# docker_compose { 'test':
#   compose_files => ['/root/ops/bankimage/docker-compose.localstorage.yml'],
#   ensure  => present,
# }

$str = "
version: '3'
services:
  db:
    image: mariadb
    volumes:
      - database:/var/lib/mysql:rw
    restart: always
    networks:
      - private
    environment:
      MYSQL_ROOT_PASSWORD: changeyourstrongpasswordhere
      MYSQL_DATABASE: imagebank
      MYSQL_USER: imagebank
      MYSQL_PASSWORD: imagebankpass
    command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8 --collation-server=utf8_general_ci
  web:
    image: imagebank
    ports:
      - 8000:8000
    depends_on:
      - db
    volumes:
      - media:/var/www/media:Z
    environment:
      DJANGO_SETTINGS_MODULE: imagebank.prod_settings
      DJANGO_MANAGEPY_MIGRATE: 'on'
      DJANGO_MANAGEPY_INITADMIN: 'on'
      DJANGO_SU_NAME: 'admin'
      DJANGO_SU_PASSWORD: 'admin@imagebank'
      DB_HOST: db
      DB_PORT: 3306
      DB_NAME: imagebank
      DB_USER: imagebank
      DB_PASSWORD: imagebankpass
    command: uwsgi imagebank/uwsgi.ini
    networks:
      - private

networks:
  private:
volumes:
  database:
  media:
"
file { "/greedfield":
    ensure  =>  directory,
    mode    =>  "0755",
}

file { '/greedfield/docker-compose.yml':
    content => $str,
    require => File["/greedfield"],
}

docker::image { 'imagebank': }