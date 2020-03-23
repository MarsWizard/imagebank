# Generated by Django 2.1.15 on 2020-03-21 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0008_auto_20200320_2255'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='album',
            name='tags',
            field=models.ManyToManyField(blank=True, to='ims.Tag'),
        ),
    ]