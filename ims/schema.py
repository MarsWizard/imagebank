from graphene import relay, ObjectType, Schema
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Album, Category


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


class Query(ObjectType):
    category = relay.Node.Field(CategoryNode)
    all_categories = DjangoFilterConnectionField(CategoryNode)

    album = relay.Node.Field(AlbumNode)
    all_albums = DjangoFilterConnectionField(AlbumNode)


schema = Schema(query=Query)
