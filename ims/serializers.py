from rest_framework.serializers import ModelSerializer
from .models import Image, ImageToFile


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'title']