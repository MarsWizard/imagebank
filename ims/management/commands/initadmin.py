import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--user')
        parser.add_argument('--password')
        parser.add_argument('--email')

    def handle(self, *args, **options):
        admin_username = options.get('user') or os.environ.get('DJANGO_SU_NAME')
        admin_email = options.get('email') or os.environ.get('DJANGO_SU_EMAIL')
        admin_password = options.get('password') or os.environ.get('DJANGO_SU_PASSWORD')

        if not admin_username:
            raise Exception("No username specified.")

        if not admin_email:
            raise Exception('No email specified.')

        if not admin_password:
            raise Exception('No password specified.')

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
