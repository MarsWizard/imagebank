from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views



urlpatterns = [
    path('api/v1/image/upload', csrf_exempt(views.UploadView.as_view()), name='ims_upload'),
    path('api/v1/albums', csrf_exempt(views.APIAlbumsView.as_view())),
    path('image/<int:image_id>', views.ImageView.as_view(), name='ims_view_image'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('upload', views.upload, name='upload'),
    path('album/<int:album_id>', views.AlbumView.as_view(), name='album_view'),
    path('albums/create', views.CreateAlbumView.as_view(), name='create_album'),
    # path('images/<int:image_id>', views.ImageView.as_view(), name='ims_view_image')
]