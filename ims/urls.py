from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('upload', csrf_exempt(views.UploadView.as_view()), name='ims_upload'),
]