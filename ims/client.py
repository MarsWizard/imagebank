import json
import logging
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth, AuthBase


logger = logging.getLogger(__name__)


class OpException(BaseException):
    def __init__(self, error_code, error_msg):
        self.error_code = error_code
        self.error_msg = error_msg


class TokenCredential(AuthBase):
    def __init__(self, token):
        self._token = token

    def __call__(self, r):
        logger.debug(r)
        r.headers['Authorization'] = f'Token {self._token}'
        return r


class ImageBankClient:
    def __init__(self, base_url, token):
        self._base_url = base_url
        self._token = token
        session = requests.Session()
        if isinstance(token, str):
            session.auth = TokenCredential(token)
        else:
            session.auth = token
        session.mount(base_url, HTTPAdapter(max_retries=5))
        session.keep_alive = False
        self._session = session

    def raise_response_error(self, response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise self._wrap_http_error(e)

    @staticmethod
    def _wrap_http_error(http_error: requests.HTTPError):
        response = http_error.response
        status_code = response.status_code
        if status_code < 400 or status_code >= 500:
            return http_error

        try:
            response_json = response.json()
        except json.decoder.JSONDecodeError:
            return http_error

        error_code = response_json.get('error_code')
        error_msg = response_json.get('error_msg')
        return OpException(error_code, error_msg)

    def get_albums(self, page_index=1):
        response = self._session.get(
            self._get_url(f'/api/v1/albums?page_index={page_index}'))
        self.raise_response_error(response)
        return json.loads(response.content)['albums']

    def get_album(self, album_id):
        response = self._session.get(
            self._get_url(f'/api/v1/album/{album_id}'))
        self.raise_response_error(response)
        return json.loads(response.content)['album']

    def find_albums(self, title=None):
        params = {}
        if title:
            params['title'] = title
        response = self._session.get(
            self._get_url(f'/api/v1/albums'), params=params)
        return response.json()

    def create_album(self, title, category=None):
        post_body = {'title': title}
        if category:
            post_body['category'] = category
        
        res = self._session.post(self._get_url(f'/api/v1/albums'), json=post_body)
        res.raise_for_status()
        return res.json()

    def save_album(self, item=None, **kwargs):
        category = kwargs.get('category')
        if not category and item:
            category = item.get('category')
        title = kwargs.get('title')
        if not title and item:
            title = item.get('title', item.get('album_title'))
        if not title:
            raise Exception("No title specified.")
        post_data = {
            'category': category,
            'title': title
        }
        tags = kwargs.get('tags', [])
        if not tags and item and 'tags' in item:
            tags = item.get('tags', [])
        post_data['tags'] = ','.join(tags)
        response = self._session.post(self._get_url('/api/v1/albums'),
                                      post_data)
        self.raise_response_error(response)
        album = json.loads(response.content)['album']
        print(response, album['id'])
        return album

    def upload_image(self, fobj=None, source=None, album_title=None,
                     album_id=None, title=None):
        file_opend = False
        files = {}
        try:
            post_data = {}
            if isinstance(fobj, str):
                f_content = open(fobj, 'rb')
                file_opend = True
                files = {'file': f_content}
            elif hasattr(fobj, 'read'):
                files = {'file': fobj}
            elif source is not None:
                post_data['source'] = source
            else:
                raise Exception('Either fobj or source should be assigned')

            if album_title:
                post_data['album_title'] = album_title
            if album_id:
                post_data['album_id'] = album_id
            if title:
                post_data['title'] = title
            response = self._session.post(
                self._get_url('/api/v1/image/upload'),
                post_data, files=files)
            self.raise_response_error(response)
            return json.loads(response.content)['image']

        finally:
            if file_opend:
                f_content.close()

    def crop_image(self, image_id, pos, shape_name):
        post_data = {
            'image_id': image_id,
            'pos': ','.join(map(str, pos)),
            'shape': shape_name
        }
        response = self._session.post(
            self._get_url('/api/v1/image/crop'),
            data=post_data)
        self.raise_response_error(response)
        return response.json()

    def _get_url(self, path):
        return urljoin(self._base_url, path)
