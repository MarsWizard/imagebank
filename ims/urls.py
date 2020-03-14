from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views



urlpatterns = [
    path('/api/v1/upload', csrf_exempt(views.UploadView.as_view()), name='ims_upload'),
    path('image/<int:image_id>', views.ImageView.as_view(), name='ims_view_image'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('upload', views.upload, name='upload'),
    path('album/<int:album_id>', views.AlbumView.as_view(), name='dashboard'),
    # path('images/<int:image_id>', views.ImageView.as_view(), name='ims_view_image')
]