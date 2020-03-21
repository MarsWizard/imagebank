import os
import logging
from io import BytesIO
from hashlib import sha1
import requests
from PIL import Image as PImage
from .models import ImageFile


SM_SIZE = (150, 150)
MD_SIZE = (350, 350)

logger = logging.getLogger(__name__)

FORMAT_EXT = {'JPEG': 'jpg', "GIF": 'gif', "PNG": 'png'}


class DownloadStream(BytesIO):
    def __init__(self, initial_bytes: bytes, url):
        self.url = url
        super(DownloadStream, self).__init__(initial_bytes)

    @property
    def name(self):
        return os.path.basename(self.url)

def get_stream_from_source(source: str):
    exist_image_file = ImageFile.objects.filter(url=source).first()
    if exist_image_file:
        return exist_image_file.photo.open()
    response = requests.get(source)
    logger.info('upload from file %s', source)
    file_stream = DownloadStream(response.content, source)
    return file_stream


def get_stream_from_upload_file(file):
    return file


def get_or_create_image_file(stream) -> ImageFile:
    logger.debug('begin save_image_file')
    stream.seek(0)
    s = sha1()
    if hasattr(stream, 'chunks'):
        for chunk in stream.chunks():
            s.update(chunk)
    else:
        s.update(stream.read())
    sha1_hash = s.hexdigest()
    stream_url = None
    if hasattr(stream, 'url'):
        stream_url = stream.url

    try:
        image_file = ImageFile.objects.get(sha1=sha1_hash)
    except ImageFile.DoesNotExist:
        stream.seek(0)
        image = PImage.open(stream)
        image_file = ImageFile()
        image_file.sha1 = sha1_hash
        image_file.width = image.width
        image_file.height = image.height
        image_file.url = stream_url
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
        stream.seek(0)
        with open(image_file.photo.path, 'wb') as dest:
            dest.write(stream.read())
        stream.seek(0, 2)
        image_file.file_size = stream.tell()
        if hasattr(stream, 'name'):
            image_file.origin_filename = stream.name
    if not image_file.url and stream_url:
        image_file.url = stream_url
    image_file.save()
    return image_file


def generate_thumbnail_file(file, size: tuple) -> ImageFile:
    image = PImage.open(file)
    image.thumbnail(size)
    buffer = BytesIO()
    image.save(buffer, format=image.format)
    image.close()
    image_file = get_or_create_image_file(buffer)
    return image_file
