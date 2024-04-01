from rest_framework import serializers
from .models import DeviceManager

class DeviceManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceManager
        fields = '__all__'