from io import BytesIO
import logging
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic.edit import CreateView
from django.views import generic
from django.urls import reverse
from django.db import transaction, IntegrityError
from rest_framework.views import APIView, Response
from .models import Album, Image, ImageToFile, Category, Tag
from .process import get_or_create_image_file, get_stream_from_source
from .process import get_stream_from_upload_file, generate_thumbnail_file, MD_SIZE, SM_SIZE
from . import serializers
from . import process
from . import exceptions

logger = logging.getLogger(__name__)

FORMAT_EXT = {'JPEG': 'jpg', "GIF": 'gif', "PNG": 'png'}

PRESERVED_SHAPES = {'origin', 'md', 'sm'}


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
        md_image_file = generate_thumbnail_file(origin_image_file.photo.open(), MD_SIZE)

    if origin_image_file.size <= SM_SIZE:
        sm_image_file = origin_image_file
    else:
        sm_image_file = generate_thumbnail_file(origin_image_file.photo.open(), SM_SIZE)
    return origin_image_file, md_image_file, sm_image_file


def upload_image(request):
    user = request.user
    if 'file' in request.FILES:
        file_stream = get_stream_from_upload_file(request.FILES['file'])
    elif 'source' in request.POST:
        file_stream = get_stream_from_source(request.POST['source'])

    title = request.POST.get('title')

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

    with transaction.atomic():
        try:
            new_image = Image.objects.get(album=album,
                                          origin_file=image_file)
            if title:
                new_image.title = title
        except Image.DoesNotExist:
            new_image = Image()
            new_image.album = album
            new_image.title = title or file_stream.name
            new_image.save()

        origin_imagetofile, created = ImageToFile.objects.get_or_create(image=new_image,
                                                               shape='origin', defaults={'file':image_file})
        if not created:
            origin_imagetofile.file = image_file
            origin_imagetofile.save()

        md_imagetofile, created = ImageToFile.objects.get_or_create(image=new_image,
                                                               shape='md', defaults={'file':medium_imagefile})
        if not created:
            md_imagetofile.file = medium_imagefile
            md_imagetofile.save()

        sm_imagetofile, created = ImageToFile.objects.get_or_create(image=new_image,
                                                               shape='sm', defaults={'file':thumbnail_imagefile})
        if not created:
            sm_imagetofile.file = thumbnail_imagefile
            sm_imagetofile.save()

        new_image.save()
    return new_image


class ApiUploadView(APIView):
    def post(self, request):
        try:
            new_image = upload_image(request)
            return JsonResponse({
                'image_id': new_image.id,
                'image': {
                    'id': new_image.id
                },
            })
        except exceptions.ImsException as e:
            return JsonResponse({
                'error_code': e.error_code,
                'error_msg': e.error_msg,
            }, status=400)


class ApiImageCropView(APIView):
    def post(self, request):
        image_id = request.POST['image_id']
        if 'pos' not in request.POST:
            return JsonResponse({'err_code': exceptions.PARAMETER_REQUIRED,
                                 'err_msg': 'pos parameter required.'},
                                status=400)
            return HttpResponseBadRequest('pos parameter not provided.')
        if 'shape' not in request.POST:
            return HttpResponseBadRequest('shape parameter not provided.')
        shape = request.POST['shape'].lower()
        if shape in PRESERVED_SHAPES:
            return HttpResponseBadRequest('shape name preserved.')
        positions = [int(x) for x in request.POST['pos'].split(',')]
        if len(positions) != 4:
            return HttpResponseBadRequest('pos should be comma separated left, top, right, bottom positions.')
        try:
            image = Image.objects.get(album__owner=request.user, pk=image_id)
        except Image.DoesNotExist:
            return HttpResponseBadRequest('image not found.')

        new_image_file = process.crop_image(image.origin_file, positions)
        try:
            old_imagetofile = ImageToFile.objects.get(image=image, shape=shape)
            old_imagetofile.file = new_image_file
            old_imagetofile.save()

        except ImageToFile.DoesNotExist:
            ImageToFile(image=image, shape=shape, file=new_image_file).save()

        return JsonResponse({'image': {'id': image.id}})


class ApiAlbumInfo(APIView):
    def get(self, request, album_id):
        try:
            album = Album.objects.get(owner=request.user,
                                     id=album_id)
        except Album.DoesNotExist:
            return JsonResponse({'err_code': exceptions.ERROR_OBJECT_NOT_FOUND,
                                 'err_msg': 'Album not found.'}, status=404)

        image_list = [{
            'id': image.id,
            'title': image.title,
            'origin': {
                'url': request.build_absolute_uri(image.origin_file.photo.url),
            },
            'md': {
                'url': request.build_absolute_uri(image.md_file.photo.url),
            },
            'sm': {
                'url': request.build_absolute_uri(image.sm_file.photo.url),
            },
            'files': {
                imagetofile.shape: {
                    'url': request.build_absolute_uri(imagetofile.file.photo.url),
                    'width': imagetofile.file.width,
                    'height': imagetofile.file.height,
                    'file_size': imagetofile.file.file_size,
                } for imagetofile in image.imagetofile_set.all()
            }
        } for image in album.image_set.all()]
        ret_data = {
            'album': {
                'id': album.id,
                'title': album.title,
                'images': image_list,
                'category': album.category.title if album.category else None,
                'tags': [x.text for x in album.tags.all()],
            }
        }
        return JsonResponse(ret_data)

    def delete(self, request, album_id):
        try:
            album = Album.objects.get(owner=request.user,
                                     id=album_id)
        except Album.DoesNotExist:
            return JsonResponse({'err_code': exceptions.ERROR_OBJECT_NOT_FOUND,
                                 'err_msg': 'Album not found.'}, status=404)
        album.delete()
        return JsonResponse({})


class ImageView(View):
    def get(self, request, image_id):
        try:
            image = Image.objects.get(album__owner=request.user, id=image_id)
        except Image.DoesNotExist:
            return HttpResponseNotFound()

        image_link = request.build_absolute_uri(reverse('ims_view_image', args=(image.id, )))
        image_url = request.build_absolute_uri(image.origin_file.photo.url)

        return render(request, 'ims/view_image.html', {'image': image, 'image_link':image_link, 'image_url': image_url})


class UploadView(LoginRequiredMixin, View):
    def get(self, request):
        if 'aid' in request.GET:
            album = Album.objects.filter(owner=request.user,
                                         pk=request.GET.get('aid')).first()
        else:
            album, _ = Album.objects.get_or_create(owner=request.user,
                                         title='default')
        return render(request, 'ims/upload.html', {'album': album})

    def post(self, request):
        new_image = upload_image(request)
        if request.is_ajax():
            return JsonResponse({
                'success': True,
                'image': {'id': new_image.id},
                'album': {'id': new_image.album.id}
            }, content_type='text/plain')
        return redirect('ims_view_image', new_image.id)


class AlbumView(LoginRequiredMixin, View):
    def get(self, request, album_id):
        album = Album.objects.get(owner=request.user, id=album_id)

        # images = [x.imagetofile_set.all()[0] for x in album.image_set.all()]
        images = album.image_set.all()
        return render(request, 'ims/album.html', {
            'album': album,
            'images': images
        })


class APIAlbumsView(APIView):
    def get(self, request):
        page_size = int(request.GET.get('page_size', 100))
        page_size = min(100, page_size)
        page_index = int(request.GET.get('page_index', 1))
        query = Album.objects.filter(owner=request.user)
        if 'title' in request.GET:
            query = query.filter(title=request.GET['title'])

        albums = query.order_by('-id')
        albums = albums[(page_index-1) * page_size:
                        page_index * page_size]

        albums_list = [{'id': album.id,
                        'title': album.title,
                        'category': album.category.title if album.category else None}
                       for album in albums]

        return JsonResponse({'albums': albums_list})

    def post(self, request):
        title = request.data['title']
        category_title = request.data.get('category')
        tags = request.data.get('tags', [])
        if isinstance(tags, str):
            tags = [x for x in tags.split(',') if x]
        user = request.user

        category = None
        if category_title:
            category, _ = Category.objects.get_or_create(owner=user, title=category_title,
                                               defaults={'owner': user,
                                                         'title': category_title})

        album, created = Album.objects.get_or_create(owner=user, title=title,
                                               defaults={'owner': user,
                                                         'title': title,
                                                         'category': category})
        request_tags = request.POST.get('tags')
        if created and request_tags:
            for tag_text in request_tags.split(','):
                tag_text = tag_text.strip()
                if not tag_text:
                    continue
                tag, _ = Tag.objects.get_or_create(text=tag_text)
                album.tags.add(tag)
            album.save()

        return JsonResponse({
            'id': album.id,
            'title': album.title,
            'category': album.category.title if album.category else None,
        })


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
        try:
            obj.save()
            return redirect('ims.album_view', obj.id)
        except IntegrityError:
            messages.add_message(self.request, messages.WARNING, 'Album with the same name already exists.')
            return self.get(self.request)


class AlbumIndexView(LoginRequiredMixin, generic.ListView):
    template_name_suffix = '_index'
    paginate_by = 24
    model = Album
    ordering = ['-create_at', '-id']

    def get_queryset(self):
        query = Album.objects.filter(owner=self.request.user)
        category_id = self.request.GET.get('cid')
        if category_id:
            query = query.filter(category_id=category_id)
        return query


class AlbumsFindJsonView(LoginRequiredMixin, View):
    def get(self, request):
        q = request.GET.get('q')

        ret_values = []
        for row in Album.objects.filter(
                owner=request.user, title__contains=q)\
                .values_list('id', 'title', named=True):
            ret_values.append({'value': row.id, 'text': row.title})

        return JsonResponse(ret_values, safe=False)


class AlbumsSearchView(AlbumIndexView):
    def get_queryset(self):
        q = self.request.GET.get('q')
        return Album.objects.filter(owner=self.request.user,
                                    title__contains=q) \
            .order_by(*self.ordering)


class ApiImageView(APIView):
    def get(self, request, image_id):
        image = Image.objects.get(album__owner=request.user, id=image_id)
        serializer = serializers.ImageSerializer(image)
        return Response(serializer.data)
