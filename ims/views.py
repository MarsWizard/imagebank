from hashlib import sha1
import os
from PIL import Image as PImage
from django.shortcuts import render
from django.http import HttpResponseForbidden, JsonResponse
from django.views import View
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import ImageFile, Album, Image, ImageToFile



# Create your views here.


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
        s = sha1()
        for chunk in upload_file.chunks():
            s.update(chunk)
        sha1_hash = s.hexdigest()

        try:
            image_file = ImageFile.objects.get(sha1=sha1_hash)
        except ImageFile.DoesNotExist:
            upload_file.seek(0)
            file_name, file_ext = os.path.splitext(upload_file.name)
            image = PImage.open(upload_file)
            image_file = ImageFile()
            image_file.sha1 = sha1_hash
            image_file.width = image.width
            image_file.height = image.height
            image_file.photo.name = '%s/%s/%s' % (sha1_hash[0:2],
                                             sha1_hash[2:4],
                                             sha1_hash[4:])
            file_path = image_file.photo.path
            file_dir = os.path.dirname(file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            upload_file.seek(0)
            with open(image_file.photo.path, 'wb') as dest:
                for chunk in upload_file.chunks():
                    dest.write(chunk)
            upload_file.seek(0, 2)
            image_file.file_size = upload_file.tell()
            image_file.origin_filename = upload_file.name
            image_file.save()

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

        image_file = image.imagetofile_set.get(sharp='origin').file

        return render(request, 'ims/view_image.html', {'image':image,
                      'image_file':image_file})



