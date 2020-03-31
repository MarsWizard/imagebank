import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.storage import DefaultStorage
from ...models import ImageFile, ImageToFile, Image


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_const', const=True)

    def handle(self, *args, **options):
        dry_run = options.pop('dry_run', False)
        storage = DefaultStorage()
        for image_file in ImageFile.objects.all():
            if storage.exists(image_file.photo.name):
                continue

            print(f'{image_file.photo.name} not found, remove imagefile {image_file.id}')

            for image_to_file in ImageToFile.objects.filter(file=image_file):
                try:
                    print(f'delete image {image_to_file.image.id}')
                    if not dry_run:
                        image_to_file.image.delete()
                except Image.DoesNotExist:
                    pass
            if not dry_run:
                image_file.delete()
