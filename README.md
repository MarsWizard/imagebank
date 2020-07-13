# imagebank 
基于django的图库程序

主要功能：
* 图集、图片、图片裁剪等操作均支持API，大部分操作为幂等操作
* 底层文件去重存储
* 多租户管理
* 支持外部二进制存储服务，CDN，独立域名绑定


# 部署
准备一个生产环境配置的prod_settings.py:

    import os
    from imagebank.settings import *

    DEBUG = False
    ALLOWED_HOSTS = [
        '*',
    ]

docker-compose.yml:

    version: '3'
    services:
      web:
        image: kevenli/imagebank
        ports:
          - "8000:8000"
        volumes:
          - media:/app/media:z
          - ./prod_settings.py:/app/imagebank/prod_settings.py:Z
          - ./logs:/app/logs:z
        environment:
          DJANGO_SETTINGS_MODULE: imagebank.prod_settings
        command: uwsgi imagebank/uwsgi.ini
    
    volumes:
      media:

## 使用mysql

prod_settings.py:

    import pymysql
    pymysql.install_as_MySQLdb()

    import dj_database_url
    DATABASES['default'] = dj_database_url.config(conn_max_age=600)

这里把pymysql安装为mysql客户端库，避免二进制库依赖，便于安装

docker-compose.yml:

    web:
      environment:
        DJANGO_MANAGEPY_MIGRATE: 'on'
        DB_HOST: db
        DB_PORT: 3306
        DATABASE_URL: mysql://user:pass@host:port/dbname

DJANGO_MANAGEPY_MIGRATE: 使用此开关可以在web启动时自动等待数据库启动完毕后运行数据库migrate操作

## 使用外部云存储服务存储图片

本系统基于django media存储图片文件，基于[django-storages](https://django-storages.readthedocs.io/en/latest/)项目可以使用外部云存储服务储存文件。

prod_settings.py:

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = '******'
    AWS_S3_REGION_NAME = '******'
    AWS_S3_ENDPOINT_URL = '******'
    AWS_ACCESS_KEY_ID = '******'
    AWS_SECRET_ACCESS_KEY = '******'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_CUSTOM_DOMAIN = '******'

具体配置项见django-storages项目文档。
