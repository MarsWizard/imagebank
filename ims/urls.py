from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views



urlpatterns = [
    path('api/v1/image/upload', views.ApiUploadView.as_view(), name='ims_upload'),
    path('api/v1/image/crop', views.ApiImageCropView.as_view()),
    path('api/v1/albums', views.APIAlbumsView.as_view()),
    path('api/v1/album/<int:album_id>', views.ApiAlbumInfo.as_view()),
    path('image/<int:image_id>', views.ImageView.as_view(), name='ims_view_image'),
    path('dashboard', views.dashboard, name='ims.dashboard'),
    path('upload', views.UploadView.as_view(), name='upload'),
    # path('upload?aid=<int:album_id>', views.UploadView.as_view(), name='ims.upload_to_album'),
    path('album/<int:album_id>', views.AlbumView.as_view(), name='ims.album_view'),
    path('albums/create', views.CreateAlbumView.as_view(), name='create_album'),
    path('albums', views.AlbumIndexView.as_view(), name='ims.album_list'),
    path('', views.HomeView.as_view(), name='ims_home')
    # path('images/<int:image_id>', views.ImageView.as_view(), name='ims_view_image')
]