from django import template
from ..models import Category

register = template.Library()


@register.simple_tag(takes_context=True)
def user_categories(context):
    user = context.request.user
    return Category.objects.filter(owner=user)


@register.simple_tag(takes_context=True)
def full_url(context, url):
    return context.request.build_absolute_uri(url)