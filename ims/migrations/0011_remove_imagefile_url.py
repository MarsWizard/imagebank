# Generated by Django 2.1.15 on 2020-03-24 11:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0010_auto_20200322_2200'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='imagefile',
            name='url',
        ),
    ]
