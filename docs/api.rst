.. _api:

API
===

Authentication
--------------
To invoke an API, client should provide information about the user's identity it represents.

There are two kinds of authentication way the APIs currently support, there's no different whichever you pick to the other
one.

Base Authentication
```````````````````
This is the RFC7617 method. https://tools.ietf.org/html/rfc7617

    HTTP Headers:

    Authorization: Basic Base64({Username}+':'+{Password})


Token Authentication
````````````````````
You can provide an API TOKEN instead of full USERNAME/PASSWORD pair.

There is no page for a non-admin user to obtain its token right now. Admin user can use admin site to view/create
token for particular user.


    HTTP Headers:

    Authorization: Token {Token}



API Endpoints
-------------


GET /api/v1/albums
````````````````````
Read albums list.

Parameters:

`page_size` (int, optional, default=100)
    maximum return records size.
`page_index` (int, optional, default=1)
    the queried page index, start with 1.

Response:
Json Format.
* albums: album list.
* albums[].id: album id.
* albums[].title: album title.
* aalbum[].category: album category title.

Example response::

    {
        "albums": [{
            "id": 1,
            "title": "album_title_1",
            "category": "test"
        },{
            "id": 2,
            "title": "album_title_2",
            "category": null
        }]
    }

GET /api/v1/album

GET /api/v1/albums/{album_id}
`````````````````````````````
Get album info.

Parameters:

* album_id(int, required): The album id.

Response:

* album: album object[object]
* album.id: album id
* album.title: album title.
* album.images: images belong to the album, Array.
* album.images[].id: image id.
* album.images[].title: image title.
* album.images[].files: image files dictionary. `shape_key`: image_file object.
    shape_key: either build-in shapes (`origin`, `md`, `sm`) or custom shape name.
    image_file object:
    * url: image file public url
    * width: image file width in pixels.
    * height: image file height in pixels.
    * file_size: the binary file length.
* album.category: album category title.
* album.tags: tags' text Array.

