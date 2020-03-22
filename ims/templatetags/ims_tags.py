from django import template

register = template.Library()


@register.simple_tag
def get_model1_object(queryset, **filters):
    if not filters:
        raise template.TemplateSyntaxError('`get_model1_object` tag requires filters.')
    return queryset.filter(**filters).first()


@register.simple_tag(takes_context=True)
def full_url(context, url):
    return context.request.build_absolute_uri(url)