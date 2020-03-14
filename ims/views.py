from hashlib import sha1
import os
from io import BytesIO
from PIL import Image as PImage
from django.shortcuts import render
from django.http import HttpResponseForbidden, JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import ImageFile, Album, Image, ImageToFile, Category

FORMAT_EXT = {'JPEG': 'jpg', "GIF": 'gif', "PNG": 'png'}

def save_image_file(upload_file):
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


class UploadView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self):
        pass


    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseForbidden()

        upload_file = request.FILES['file']

        image_file = save_image_file(upload_file)

        if 'album' in request.POST:
            album = Album.objects.get(owner=user, title=request.POST['album'])
        else:
            album, _ = Album.objects.get_or_create(owner=user, title='default',
                                                defaults={'owner': user,
                                                          'title': 'default'})


        exist_images = Image.objects.filter(album=album,
                                           imagetofile__file__exact=image_file)
        if exist_images:
            new_image = exist_images[0]
        else:
            new_image = Image()
            new_image.album = album
            new_image.title = os.path.splitext(upload_file.name)[0]
            new_image.save()
            new_image_to_file = ImageToFile(image=new_image, file=image_file, sharp='origin')
            new_image_to_file.save()
            new_image.imagetofile_set.add(new_image_to_file)
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

    return render(request, 'ims/dashboard.html', {'albums': albums})


def gen_thumbnail_image_file(image):
    thumbnail_image = image.crop((150,150))



@login_required
def upload(request):
    if request.method == 'POST':
        user = request.user
        upload_file = request.FILES['file']
        image_file = save_image_file(upload_file)

        if 'album' in request.POST:
            album = Album.objects.get(owner=user, id=request.POST['album'])
        else:
            album, _ = Album.objects.get_or_create(owner=user,
                                                   title='default',
                                                   defaults={'owner': user,
                                                             'title': 'default'})

        try:
            new_image = Image.objects.get(album=album,
                                            imagetofile__file__exact=image_file)
        except Image.DoesNotExist:
            new_image = Image()
            new_image.album = album
            new_image.title = os.path.splitext(upload_file.name)[0]
            new_image.save()
            #new_image_to_file = ImageToFile(image=new_image, file=image_file,
            #                                shape='origin')
            #new_image_to_file.save()
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

            #new_image.imagetofile_set.add(new_image_to_file)
            #new_image.imagetofile_set.add(thumbnail_imagefile)
            #new_image.imagetofile_set.add(medium_imagefile)
        new_image.save()

    albums = Album.objects.filter(owner=request.user).all()
    return render(request, 'ims/upload.html', {'albums': albums})


class AlbumView(LoginRequiredMixin, View):
    def get(self, request, album_id):
        album = Album.objects.get(owner=request.user, id=album_id)

        # images = [x.imagetofile_set.all()[0] for x in album.image_set.all()]
        images = album.image_set.all()
        return render(request, 'ims/album.html', {'images': images})


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