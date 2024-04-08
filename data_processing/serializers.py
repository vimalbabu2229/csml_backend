from rest_framework import serializers
from .models import DeviceManager, ForecastModel

class DeviceManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceManager
        fields = '__all__'

class FileUploadSerializer(serializers.Serializer):
    audio = serializers.FileField(max_length=None, allow_empty_file=False)
    
class ForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastModel
        fields = '__all__'