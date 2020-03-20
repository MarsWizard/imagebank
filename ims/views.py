from hashlib import sha1
import os
from io import BytesIO
import logging
import math
from PIL import Image as PImage
import requests
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.views import generic
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import ImageFile, Album, Image, ImageToFile, Category
from .process import get_or_create_image_file, get_stream_from_source
from .process import get_stream_from_upload_file, generate_thumbnail_file, MD_SIZE, SM_SIZE
from . import process

logger = logging.getLogger(__name__)

FORMAT_EXT = {'JPEG': 'jpg', "GIF": 'gif', "PNG": 'png'}


def upload_file_images(file=None, source=None):
    """
    Generate system image files for uploaded file
    :param file: uploaded stream
    :param source: the url need to be downloaded
    :return:
    """
    if source:
        response = requests.get(source)
        upload_file = BytesIO(response.content)
    elif file:
        upload_file = file
    origin_image_file = get_or_create_image_file(upload_file)
    if origin_image_file.size <= MD_SIZE:
        md_image_file = origin_image_file
    else:
        md_image_file = generate_thumbnail_file(origin_image_file.photo.file, MD_SIZE)

    if origin_image_file.size <= SM_SIZE:
        sm_image_file = origin_image_file
    else:
        sm_image_file = generate_thumbnail_file(origin_image_file.photo.file, SM_SIZE)
    return origin_image_file, md_image_file, sm_image_file


class ApiUploadView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if 'file' in request.FILES:
            file_stream = get_stream_from_upload_file(request.FILES['file'])
        elif 'source' in request.POST:
            file_stream = get_stream_from_source(request.POST['source'])

        if 'album_id' in request.POST:
            album = Album.objects.get(owner=user, id=request.POST['album_id'])
        elif 'album' in request.POST:
            album_title = request.POST['album']
            album, _ = Album.objects.get_or_create(owner=user, title=album_title)
        else:
            album, _ = Album.objects.get_or_create(owner=user, title='default',
                                                defaults={'owner': user,
                                                          'title': 'default'})
        image_file, medium_imagefile, thumbnail_imagefile = upload_file_images(
            file_stream)
        try:
            new_image = Image.objects.get(album=album,
                                          origin_file=image_file)
        except Image.DoesNotExist:
            new_image = Image()
            new_image.album = album
            new_image.title = file_stream.name
            new_image.save()
            new_image.origin_file = image_file
            new_image.sm_file = thumbnail_imagefile
            new_image.md_file = medium_imagefile
            new_image.save()

        return JsonResponse({'image_id': new_image.id})


class ImageView(View):
    def get(self, request, image_id):
        image = Image.objects.get(id=image_id)
        if image.album.owner.id != request.user.id:
            return HttpResponseForbidden()

        image_link = request.build_absolute_uri(reverse('ims_view_image', args=(image.id, )))
        image_url = request.build_absolute_uri(image.origin_file.photo.url)

        # image_file = image.imagetofile_set.get(sharp='origin').file

        return render(request, 'ims/view_image.html', {'image': image, 'image_link':image_link, 'image_url': image_url})


@login_required
def dashboard(request):
    page_size = int(request.GET.get('pagesize', 25))
    page_index = int(request.GET.get('pageindex', 1))
    sort_by = request.GET.get('sortby', 'title')
    sort_dir = request.GET.get('sortdir', '1')
    sort_chars = {'1':'', '2':'-'}
    albums = Album.objects.filter(owner=request.user)
    album_count = albums.count()
    page_count = math.ceil(album_count / page_size)
    albums = albums.order_by(sort_chars[sort_dir] + sort_by)
    albums = albums[(page_index-1) * page_size: page_index * page_size]



    return render(request, 'ims/dashboard.html',
                  {
                      'albums': albums,
                      'page_count': page_count,
                      'page_index': page_index,
                      'page_size': page_size})


def gen_thumbnail_image_file(image):
    thumbnail_image = image.crop((150,150))


class UploadView(LoginRequiredMixin, View):
    def get(self, request):
        album_id = int(request.GET.get('aid', 0))
        albums = Album.objects.filter(owner=request.user).all()
        return render(request, 'ims/upload.html', {'albums': albums, 'album_id': album_id})

    def post(self, request):
        user = request.user
        if 'file' in request.FILES:
            file_stream = get_stream_from_upload_file(request.FILES['file'])
        elif 'source' in request.POST:
            file_stream = get_stream_from_source(request.POST['source'])

        image_file, medium_imagefile, thumbnail_imagefile = upload_file_images(
            file_stream)

        if 'album_id' in request.POST:
            album = Album.objects.get(owner=user, id=request.POST['album_id'])
        else:
            album, _ = Album.objects.get_or_create(owner=user,
                                                   title='default',
                                                   defaults={'owner': user,
                                                             'title': 'default'})

        try:
            new_image = Image.objects.get(album=album,
                                          origin_file=image_file)
        except Image.DoesNotExist:
            new_image = Image()
            new_image.album = album
            new_image.title = file_stream.name
            new_image.save()
            new_image.origin_file = image_file
            new_image.sm_file = thumbnail_imagefile
            new_image.md_file = medium_imagefile
            new_image.save()
        if request.is_ajax():
            return JsonResponse({
                'image': {'id': new_image.id},
                'album': {'id': album.id}
            })
        return redirect('ims_view_image', new_image.id)



@login_required
def upload(request):
    if request.method == 'POST':
        user = request.user
        if 'file' in request.FILES:
            file_stream = get_stream_from_upload_file(request.FILES['file'])
        elif 'source' in request.POST:
            file_stream = get_stream_from_source(request.POST['source'])

        image_file, medium_imagefile, thumbnail_imagefile = upload_file_images(
            file_stream)

        if 'album_id' in request.POST:
            album = Album.objects.get(owner=user, id=request.POST['album_id'])
        else:
            album, _ = Album.objects.get_or_create(owner=user,
                                                   title='default',
                                                   defaults={'owner': user,
                                                             'title': 'default'})

        try:
            new_image = Image.objects.get(album=album,
                                            origin_file=image_file)
        except Image.DoesNotExist:
            new_image = Image()
            new_image.album = album
            new_image.title = file_stream.name
            new_image.save()
            new_image.origin_file = image_file
            new_image.sm_file = thumbnail_imagefile
            new_image.md_file = medium_imagefile
            new_image.save()
        if request.is_ajax():
            return JsonResponse({
                'image': {'id': new_image.id},
                'album': {'id': album.id}
            })
        return redirect('ims_view_image', new_image.id)

    albums = Album.objects.filter(owner=request.user).all()
    return render(request, 'ims/upload.html', {'albums': albums})


class AlbumView(LoginRequiredMixin, View):
    def get(self, request, album_id):
        album = Album.objects.get(owner=request.user, id=album_id)

        # images = [x.imagetofile_set.all()[0] for x in album.image_set.all()]
        images = album.image_set.all()
        return render(request, 'ims/album.html', {
            'album': album,
            'images': images
        })


def login(self, request):
    pass

def logout(self, request):
    pass


class APIAlbumsView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pass

    def post(self, request):
        title = request.POST['title']
        category_title = request.POST.get('category')
        user = request.user

        category = None
        if category_title:
            category, _ = Category.objects.get_or_create(owner=user, title=category_title,
                                               defaults={'owner': user,
                                                         'title': category_title})

        album, _ = Album.objects.get_or_create(owner=user, title=title,
                                               defaults={'owner': user,
                                                         'title': title,
                                                         'category': category})

        return JsonResponse({'album':{
            'id': album.id,
            'title': album.title,
            'category': album.category.title if album.category else None,
        }})

class CreateAlbumView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'ims/createalbum.html')

    def post(self, request):
        title = request.POST['title']

        album = Album(title=title, owner=request.user)
        album.save()
        return redirect('album_view', album.id)


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'ims/home.html')


class CreateAlbumView(LoginRequiredMixin, CreateView):
    model = Album
    template_name_suffix = '_create_form'
    fields = ['category', 'title']

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user
        obj.save()
        return redirect('ims.dashboard')

class AlbumIndexView(generic.ListView):
    template_name_suffix = '_index'
    paginate_by = 24
    ordering = ['-create_at']

    def get_queryset(self):
        return Album.objects.filter(owner=self.request.user)\
            .order_by(*self.ordering)
