"""imagebank URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.views.static import serve
from django.conf import settings
from django.http import FileResponse

def static_file_no_ext_serve(view_func):
    """Mark a view function as being exempt from the CSRF view protection."""
    # view_func.csrf_exempt = True would also work, but decorators are nicer
    # if they don't have side effects, so return a new function.
    def wrapped_view(*args, **kwargs):
        path = kwargs.pop('path')
        path = os.path.splitext(path)[0]
        kwargs['path'] = path
        response = view_func(*args, **kwargs)
        if isinstance(response, FileResponse):
            response['Content-Type'] = 'image/jpeg'
            return response
        return response
    return wrapped_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('ims.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#+ static('images', document_root='media', view=static_file_no_ext_serve(serve))
# + static('images', document_root='media')
