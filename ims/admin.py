from django.contrib import admin
from .models import ImageFile, Image, Category, Album

# Register your models here.

class ImageAdminView(admin.ModelAdmin):
    list_display = ['album']

class AlbumAdminView(admin.ModelAdmin):
    list_display = ['title']

admin.site.register(Category)
admin.site.register(Album, AlbumAdminView)
# admin.site.register(ImageFile)
admin.site.register(Image, ImageAdminView)
