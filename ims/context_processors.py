from .models import Category

def categories(request):
    if request.user.is_authenticated:
        data = Category.objects.filter(owner=request.user)
    else:
        data = []

    return {
        'categories': data
    }
