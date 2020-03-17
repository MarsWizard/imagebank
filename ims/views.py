from hashlib import sha1
import os
from io import BytesIO
import logging
from PIL import Image as PImage
import requests
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import ImageFile, Album, Image, ImageToFile, Category
from .process import get_or_create_image_file, get_stream_from_source, get_stream_from_upload_file, generate_thumbnail_file

logger = logging.getLogger(__name__)

FORMAT_EXT = {'JPEG': 'jpg', "GIF": 'gif', "PNG": 'png'}

def save_image_file(upload_file):
    logger.debug('begin save_image_file')
    s = sha1()
    if hasattr(upload_file, 'chunks'):
        for chunk in upload_file.chunks():
            s.update(chunk)
    else:
        s.update(upload_file.read())
    sha1_hash = s.hexdigest()

    try:
        image_file = ImageFile.objects.get(sha1=sha1_hash)
    except ImageFile.DoesNotExist:
        upload_file.seek(0)
        image = PImage.open(upload_file)
        image_file = ImageFile()
        image_file.sha1 = sha1_hash
        image_file.width = image.width
        image_file.height = image.height
        image_file_ext = '.' + FORMAT_EXT[image.format] if image.format else ''
        image_file.photo.name = '%s/%s/%s%s' % (sha1_hash[0:2],
                                                sha1_hash[2:4],
                                                sha1_hash[4:],
                                                image_file_ext)
        image_file.format = image.format
        file_path = image_file.photo.path
        file_dir = os.path.dirname(file_path)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        upload_file.seek(0)
        with open(image_file.photo.path, 'wb') as dest:
            dest.write(upload_file.read())
        upload_file.seek(0, 2)
        image_file.file_size = upload_file.tell()
        if hasattr(upload_file, 'name'):
            image_file.origin_filename = upload_file.name
        image_file.save()
    return image_file


SM_SIZE = (150, 150)
MD_SIZE = (350, 350)


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
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self):
        pass


    def post(self, request):
        user = request.user

        upload_file = request.FILES['file']

        image_file = save_image_file(upload_file)
        logger.debug('save_image_file done')

        if 'album_id' in request.POST:
            album = Album.objects.get(owner=user, id=request.POST['album'])
        elif 'album' in request.POST:
            album_title = request.POST['album']
            album, _ = Album.objects.get_or_create(owner=user, title='album_title',
                                                   defaults={'owner': user,
                                                             'title': album_title})
        else:
            album, _ = Album.objects.get_or_create(owner=user, title='default',
                                                defaults={'owner': user,
                                                          'title': 'default'})
        try:
            new_image = Image.objects.get(album=album,
                                          origin_file=image_file)
        except Image.DoesNotExist:
            new_image = Image()
            new_image.album = album
            new_image.title = os.path.splitext(upload_file.name)[0]
            new_image.save()
            # new_image_to_file = ImageToFile(image=new_image, file=image_file,
            #                                shape='origin')
            # new_image_to_file.save()
            new_image.origin_file = image_file
            new_image.save()

        if new_image.sm_file is None:
            upload_file.seek(0)
            image = PImage.open(upload_file)
            image.thumbnail((150, 150))
            thumbnail_buffer = BytesIO()
            image.save(thumbnail_buffer, format='JPEG')
            thumbnail_buffer.seek(0)
            thumbnail_imagefile = save_image_file(thumbnail_buffer)
            thumbnail_imagefile.save()
            new_image.sm_file = thumbnail_imagefile

        if new_image.md_file is None:
            image = PImage.open(upload_file)
            image.thumbnail((350, 350))
            medium_buffer = BytesIO()
            image.save(medium_buffer, format='JPEG')
            medium_buffer.seek(0)
            medium_imagefile = save_image_file(medium_buffer)
            new_image.md_file = medium_imagefile

            # new_image.imagetofile_set.add(new_image_to_file)
            # new_image.imagetofile_set.add(thumbnail_imagefile)
            # new_image.imagetofile_set.add(medium_imagefile)
        new_image.save()

        return JsonResponse({'image_id': new_image.id})


class ImageView(View):
    def get(self, request, image_id):
        image = Image.objects.get(id=image_id)
        if image.album.owner.id != request.user.id:
            return HttpResponseForbidden()

        # image_file = image.imagetofile_set.get(sharp='origin').file

        return render(request, 'ims/view_image.html', {'image': image})


@login_required
def dashboard(request):
    albums = Album.objects.filter(owner=request.user)

    return render(request, 'ims/dashboard.html',
                  {'albums': albums})


def gen_thumbnail_image_file(image):
    thumbnail_image = image.crop((150,150))



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
