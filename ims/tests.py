import os
import re
from io import BytesIO
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from ims.views import upload_file_images, SM_SIZE, MD_SIZE
from ims.models import Image, Album
from ims.process import crop_image, get_or_create_image_file
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

BASE_DIR = os.path.dirname(__file__)


class ApiTestBase(TestCase):
    def setUp(self) -> None:
        user, _ = User.objects.get_or_create(username='testuser')
        token, _ = Token.objects.get_or_create(user=user)
        Album.objects.filter(owner=user).delete()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.client = client
        self.user = user


class WebViewTestBase(TestCase):
    def setUp(self) -> None:
        user, _ = User.objects.get_or_create(username='testuser')
        self.client.force_login(user)
        self.user = user


class UploadViewTest(TestCase):
    def setUp(self):
        self.client.force_login(
            User.objects.get_or_create(username='testuser')[0])

    def test_get(self):
        response = self.client.get('/upload')
        self.assertEqual(200, response.status_code)

    def test_post(self):
        file_to_upload = open(os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'), 'rb')
        response = self.client.post('/upload', {
            'file': file_to_upload})
        self.assertEqual(302, response.status_code)
        redirect_url = response['Location']
        self.assertIsNotNone(redirect_url)
        m = re.search(r'/image/(\d+)', redirect_url)
        new_image_id = int(m.group(1))
        self.assertIsNotNone(new_image_id)
        new_image = Image.objects.get(pk=new_image_id)
        self.assertEqual('wallpaper_tree.jpg', new_image.title)
        self.assertIsNotNone(new_image.origin_file)
        self.assertIsNotNone(new_image.md_file)
        self.assertTrue(new_image.md_file.size <= MD_SIZE)
        self.assertIsNotNone(new_image.sm_file)
        self.assertTrue(new_image.sm_file.size <= SM_SIZE)

    def test_post_ajax(self):
        file_to_upload = open(os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'), 'rb')
        response = self.client.post('/upload', {
            'file': file_to_upload},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)



    def test_post_source(self):
        response = self.client.post('/upload', {
            'source': 'https://www.python.org/static/img/python-logo.png'})
        self.assertEqual(302, response.status_code)


class APIUploadTest(TestCase):
    def setUp(self):
        user, _ = User.objects.get_or_create(username='testuser')
        token, _ = Token.objects.get_or_create(user=user)
        Album.objects.filter(owner=user).delete()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.client = client
        self.user = user

    def test_post(self):
        file_to_upload = open(os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'), 'rb')

        response = self.client.post('/api/v1/image/upload', {
            'file': file_to_upload})
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        new_image = Image.objects.get(pk=new_image_id)
        self.assertEqual('wallpaper_tree.jpg', new_image.title)
        self.assertIsNotNone(new_image.origin_file)
        self.assertIsNotNone(new_image.md_file)
        self.assertTrue(new_image.md_file.size <= MD_SIZE)
        self.assertIsNotNone(new_image.sm_file)
        self.assertTrue(new_image.sm_file.size <= SM_SIZE)
        image_files = {imagetofile.shape: imagetofile.file for imagetofile in new_image.imagetofile_set.all()}

        self.assertIn('origin', image_files)
        self.assertIn('md', image_files)
        self.assertIn('sm', image_files)

    def test_noauth(self):
        self.client.credentials()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
            'file': file_to_upload})
        self.assertEqual(401, response.status_code)

    def test_upload_with_album(self):
        album = 'test_album'
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload',
                                    {
                                        'file': file_to_upload,
                                        'album': album
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']
        new_image = Image.objects.get(pk=new_image_id)
        self.assertEqual(new_image.album.title, album)

    def test_upload_with_title(self):
        Image.objects.filter(album__owner=self.user).delete()
        album = 'test_album'
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload',
                                    {
                                        'file': file_to_upload,
                                        'album': album,
                                        'title': 'xx.jpg'
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']
        new_image = Image.objects.get(pk=new_image_id)
        self.assertEqual(new_image.album.title, album)
        self.assertEqual(new_image.title, 'xx.jpg')

    def test_upload_source(self):
        response = self.client.post('/api/v1/image/upload',
                                    {
                                        'source': 'https://www.python.org/static/img/python-logo.png',
                                    })
        self.assertEqual(200, response.status_code)

    def test_upload_to_album_id(self):
        album, _ = Album.objects.get_or_create(title='test_upload_to_album_id', owner=self.user)
        with open(os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'), 'rb') as f:
            response = self.client.post('/api/v1/image/upload',
                                        {
                                            'file': f,
                                            'album_id': album.id,
                                        })
        self.assertEqual(200, response.status_code)

    def test_upload_overwrite_existing_title(self):
        with open(
                os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
                'rb') as f:
            response = self.client.post('/api/v1/image/upload',
                                        {
                                            'file': f,
                                            'title': '1.jpg'
                                        })
            self.assertEqual(200, response.status_code)
            f.seek(0)
            response = self.client.post('/api/v1/image/upload',
                                        {
                                            'file': f,
                                            'title': '2.jpg'
                                        })
            self.assertEqual(200, response.status_code)
            image_id = json.loads(response.content)['image_id']
            image = Image.objects.get(pk=image_id)
            self.assertEqual(image.title, '2.jpg')


class ApiImageCropTest(ApiTestBase):
    def test_post(self):
        Image.objects.filter(album__owner=self.user).delete()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
                                        'file': file_to_upload,
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        response = self.client.post('/api/v1/image/crop', {
            'image_id': new_image_id,
            'pos': '0,0,300,300',
            'shape': 'square'
        })
        self.assertEqual(200, response.status_code)
        new_image = Image.objects.get(pk=new_image_id)
        image_files = {imagetofile.shape: imagetofile.file for imagetofile in new_image.imagetofile_set.all()}
        self.assertIn('square', image_files)

    def test_post_overwrite(self):
        Image.objects.filter(album__owner=self.user).delete()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
                                        'file': file_to_upload,
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        response = self.client.post('/api/v1/image/crop', {
            'image_id': new_image_id,
            'pos': '0,0,300,300',
            'shape': 'square'
        })
        response = self.client.post('/api/v1/image/crop', {
            'image_id': new_image_id,
            'pos': '0,0,300,300',
            'shape': 'square'
        })
        self.assertEqual(200, response.status_code)
        new_image = Image.objects.get(pk=new_image_id)
        image_files = {imagetofile.shape: imagetofile.file for imagetofile in new_image.imagetofile_set.all()}
        self.assertIn('square', image_files)

    def test_post_invalid_pos(self):
        Image.objects.filter(album__owner=self.user).delete()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
                                        'file': file_to_upload,
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        response = self.client.post('/api/v1/image/crop', {
            'image_id': new_image_id,
            'pos': '0,0,300',
            'shape': 'square'
        })
        self.assertEqual(400, response.status_code)

    def test_post_no_pos(self):
        Image.objects.filter(album__owner=self.user).delete()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
                                        'file': file_to_upload,
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        response = self.client.post('/api/v1/image/crop', {
            'image_id': new_image_id,
            'shape': 'square'
        })
        self.assertEqual(400, response.status_code)
        response_body = json.loads(response.content)
        self.assertEqual(10002, response_body['err_code'])

    def test_post_no_shape(self):
        Image.objects.filter(album__owner=self.user).delete()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
                                        'file': file_to_upload,
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        response = self.client.post('/api/v1/image/crop', {
            'image_id': new_image_id,
            'pos': '0,0,300,300',
        })
        self.assertEqual(400, response.status_code)

    def test_post_reserved_shape(self):
        Image.objects.filter(album__owner=self.user).delete()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
                                        'file': file_to_upload,
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        response = self.client.post('/api/v1/image/crop', {
            'image_id': new_image_id,
            'pos': '0,0,300,300',
            'shape': 'md'
        })
        self.assertEqual(400, response.status_code)

    def test_post_no_image(self):
        Image.objects.filter(album__owner=self.user).delete()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
                                        'file': file_to_upload,
                                    })
        self.assertEqual(200, response.status_code)
        new_image_id = json.loads(response.content)['image_id']

        response = self.client.post('/api/v1/image/crop', {
            'image_id': 9999,
            'pos': '0,0,300,300',
            'shape': 'square'
        })
        self.assertEqual(400, response.status_code)


class UploadImageImagesTest(TestCase):
    def test_upload_file_images(self):
        with open(os.path.join(BASE_DIR, '..', 'static/img/loading.gif'), 'rb') as f:
            buffer = BytesIO(f.read())
        origin_image_file, md_image_file, sm_image_file = upload_file_images(buffer)
        self.assertIsNotNone(origin_image_file)
        self.assertEqual(origin_image_file.format, 'GIF')
        self.assertIsNotNone(md_image_file)
        self.assertIsNotNone(sm_image_file)

    def test_upload_file_images_source(self):
        source = 'https://www.python.org/static/img/python-logo.png'
        origin_image_file, md_image_file, sm_image_file = upload_file_images(source=source)
        self.assertIsNotNone(origin_image_file)
        self.assertEqual(origin_image_file.format, 'PNG')
        self.assertIsNotNone(md_image_file)
        self.assertIsNotNone(sm_image_file)


class ProcessTest(TestCase):
    def test_crop(self):
        positions = (0, 0, 350, 350)
        with open(os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'), 'rb') as f:
            buffer = BytesIO(f.read())

        origin_imagefile = get_or_create_image_file(buffer)
        cropped_imagefile = crop_image(origin_imagefile, positions)

        self.assertTrue(cropped_imagefile.size == (350, 350))


class HomeViewTest(TestCase):
    def setUp(self):
        user, _ = User.objects.get_or_create(username='testuser')
        self.client.force_login(user)

    def test_get(self):
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)

    def test_get_nologin(self):
        self.client.logout()
        response = self.client.get('/')
        self.assertEqual(302, response.status_code)
        self.assertEqual('/accounts/login/?next=/', response['location'])


class CreateAlbumViewTest(TestCase):
    def setUp(self):
        user, _ = User.objects.get_or_create(username='testuser')
        self.user = user
        self.client.force_login(user)

    def test_post(self):
        response = self.client.post('/albums/create', {'category': '',
                                            'title': 'CreateAlbumViewTest'})
        self.assertEqual(302, response.status_code)
        saved_album = Album.objects.last()
        self.assertEqual(saved_album.title, "CreateAlbumViewTest")
        self.assertEqual(saved_album.owner, self.user)
        self.assertEqual(saved_album.category, None)


class ApiAlbumInfoTest(ApiTestBase):
    def test_get(self):
        response = self.client.post('/api/v1/albums', {'title': 'ApiAlbumInfoTest'})
        self.assertEqual(200, response.status_code)
        album_id = json.loads(response.content)['album']['id']
        response = self.client.get('/api/v1/album/%s' % album_id)
        self.assertEqual(200, response.status_code)
        album_info = json.loads(response.content)['album']

        self.assertEqual(album_id, album_info['id'])
        self.assertEqual('ApiAlbumInfoTest', album_info['title'])

    def test_get_not_exist(self):
        album_id = 9999
        response = self.client.get('/api/v1/album/%s' % album_id)
        self.assertEqual(404, response.status_code)


class ImageViewTest(WebViewTestBase):
    def test_get(self):
        file_to_upload = open(os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'), 'rb')
        response = self.client.post('/upload', {
            'file': file_to_upload})
        self.assertEqual(302, response.status_code)
        redirect_url = response['Location']
        self.assertIsNotNone(redirect_url)
        m = re.search(r'/image/(\d+)', redirect_url)
        new_image_id = int(m.group(1))
        response = self.client.get('/image/%s' % new_image_id)
        self.assertEqual(200, response.status_code)

    def test_get_image_not_found(self):
        new_image_id = 9999
        response = self.client.get('/image/%s' % new_image_id)
        self.assertEqual(404, response.status_code)

