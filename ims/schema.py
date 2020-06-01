from graphene import relay, ObjectType, Schema, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Album, Category, Image, ImageFile


class CategoryNode(DjangoObjectType):
    class Meta:
        model = Category
        filter_fields = {'title'}
        interfaces = (relay.Node, )

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(owner=info.context.user)


class AlbumNode(DjangoObjectType):
    class Meta:
        model = Album
        filter_fields = {
            'title': ['exact', 'icontains', 'istartswith'],
            'category__id': ['exact'],
            'category__title': ['exact'],
        }
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(owner=info.context.user)


class ImageNode(DjangoObjectType):
    class Meta:
        model = Image
        fields = ['title', 'files']
        interfaces = (relay.Node, )


class ImageFileNode(DjangoObjectType):
    url = String()

    class Meta:
        model = ImageFile
        interfaces = (relay.Node,)
        fields = ['url']

    def resolve_url(self, info):
        return self.photo.url


class Query(ObjectType):
    category = relay.Node.Field(CategoryNode)
    all_categories = DjangoFilterConnectionField(CategoryNode)

    album = relay.Node.Field(AlbumNode)
    all_albums = DjangoFilterConnectionField(AlbumNode)


schema = Schema(query=Query)
