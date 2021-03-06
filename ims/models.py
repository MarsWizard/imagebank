from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models import signals


class Category(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=False)

    class Meta:
        unique_together = [
            ['owner', 'title'],
        ]

    def __str__(self):
        return self.title


class Tag(models.Model):
    text = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.text


class Album(models.Model):
    owner = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True)
    title = models.CharField(max_length=255, null=False)
    create_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        unique_together = [
            ['owner', 'title']
        ]

    def __str__(self):
        return self.title


class ImageFile(models.Model):
    sha1 = models.CharField(max_length=40, unique=True)
    photo = models.ImageField(upload_to='images')
    width = models.IntegerField(null=False)
    height = models.IntegerField(null=False)
    file_size = models.IntegerField(null=False)
    origin_filename = models.CharField(max_length=255)
    format = models.CharField(max_length=4, null=True)

    @property
    def size(self):
        return self.width, self.height


class Image(models.Model):
    album = models.ForeignKey(Album, null=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=False)
    origin_file = models.ForeignKey(ImageFile, null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='origin')
    md_file = models.ForeignKey(ImageFile, null=True,
                                on_delete=models.SET_NULL, related_name='md')
    sm_file = models.ForeignKey(ImageFile, null=True,
                                on_delete=models.SET_NULL, related_name='sm')
    files = models.ManyToManyField(ImageFile, through='ImageToFile')


class ImageToFile(models.Model):
    image = models.ForeignKey(Image, null=False, on_delete=models.CASCADE)
    file = models.ForeignKey(ImageFile, null=False, on_delete=models.PROTECT)
    shape = models.CharField(max_length=10)

    class Meta:
        unique_together = [
            ['image', 'shape'],
        ]


@receiver(signals.post_save, sender=ImageToFile)
def update_image_files(sender, instance: ImageToFile = None, **kwargs):
    if instance.shape == 'origin':
        instance.image.origin_file = instance.file
        instance.image.save()

    if instance.shape == 'md':
        instance.image.md_file = instance.file
        instance.image.save()

    if instance.shape == 'sm':
        instance.image.sm_file = instance.file
        instance.image.save()
