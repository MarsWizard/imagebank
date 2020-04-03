import json
import logging
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth, AuthBase


logger = logging.getLogger(__name__)


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

    def get_albums(self, page_index=1):
        response = self._session.get(
            self._get_url(f'/api/v1/albums?page_index={page_index}'))
        response.raise_for_status()
        return json.loads(response.content)['albums']

    def get_album(self, album_id):
        response = self._session.get(
            self._get_url(f'/api/v1/album/{album_id}'))
        response.raise_for_status()
        return json.loads(response.content)['album']

    def save_album(self, item=None, **kwargs):
        category = kwargs.get('category') or item.get('category')
        title = kwargs.get('title', item.get('title'))
        title = title or kwargs.get('album_title', item.get('album_title'))
        post_data = {'category': category,
                     'title': title
                     }
        if 'tags' in item:
            post_data['tags'] = ','.join(item['tags'])
        response = self._session.post(self._get_url('/api/v1/albums'),
                                      post_data)
        response.raise_for_status()
        album_id = json.loads(response.content)['album']['id']
        print(response, album_id)
        return album_id

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
            response.raise_for_status()
            return json.loads(response.content)

        finally:
            if file_opend:
                f_content.close()

    def _get_url(self, path):
        return urljoin(self._base_url, path)
