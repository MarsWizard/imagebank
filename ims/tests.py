import os
import re
from io import BytesIO
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from ims.views import upload_file_images, SM_SIZE, MD_SIZE
from ims.models import Image
from ims.process import crop_image, get_or_create_image_file
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

BASE_DIR = os.path.dirname(__file__)


class UploadViewTest(TestCase):
    def setUp(self):
        self.client.force_login(
            User.objects.get_or_create(username='testuser')[0])

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

    def test_noauth(self):
        self.client.credentials()
        file_to_upload = open(
            os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'),
            'rb')

        response = self.client.post('/api/v1/image/upload', {
            'file': file_to_upload})
        self.assertEqual(403, response.status_code)

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
    def text_crop(self):
        positions = (0, 0, 350, 350)
        with open(os.path.join(BASE_DIR, '..', 'static/img/wallpaper_tree.jpg'), 'rb') as f:
            buffer = BytesIO(f.read())

        origin_imagefile = get_or_create_image_file(buffer)
        cropped_imagefile = crop_image(origin_imagefile, positions)

        self.assertTrue(cropped_imagefile.size == (350, 350))
