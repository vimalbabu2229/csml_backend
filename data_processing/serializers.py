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

class ForecastStatsSerializer(serializers.Serializer):
    device = serializers.IntegerField()
    average_forecast = serializers.IntegerField()
    min_noise_level = serializers.IntegerField()
    max_noise_level = serializers.IntegerField()
    average_noise_level = serializers.IntegerField()