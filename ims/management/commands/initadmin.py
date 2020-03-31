import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        admin_username = os.environ.get('DJANGO_SU_NAME', 'admin')
        admin_email = os.environ.get('DJANGO_SU_EMAIL', 'admin@localhost.com')
        admin_password = os.environ.get('DJANGO_SU_PASSWORD', 'admin')
        if User.objects.filter(username=admin_username).first():
            print(f'{admin_username} user already exists.')
            return

        admin_user = User.objects.create_superuser(username=admin_username,
                                                   email=admin_email,
                                                   password=admin_password)
        admin_user.is_active = True
        admin_user.is_admin = True
        admin_user.save()
        print(f'{admin_username} user created.')
