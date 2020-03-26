from django.contrib import admin
from .models import ImageFile, Image, Category, Album, Tag


class ImageAdminView(admin.ModelAdmin):
    list_display = ['album']


class AlbumAdminView(admin.ModelAdmin):
    list_display = ['id', 'title', 'owner']
    filter_horizontal = ['tags']
    search_fields = ['title']


admin.site.register(Category)
admin.site.register(Album, AlbumAdminView)
# admin.site.register(ImageFile)
admin.site.register(Image, ImageAdminView)
admin.site.register(Tag)
