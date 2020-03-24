# imagebank 
只是一个图库程序

主要功能：
* 图集、图片、图片裁剪等操作均支持API
* 底层文件去重存储
* 不同用户数据隔离


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
        image: kevenli/imagebank
        ports:
          - "8000:8000"
        depends_on:
          - db
        volumes:
          - media:/var/www/media:Z
        environment:
          DJANGO_SETTINGS_MODULE: imagebank.prod_settings
          DJANGO_MANAGEPY_MIGRATE: 'on'
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