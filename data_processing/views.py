from rest_framework.views import APIView
from rest_framework.response import Response    
from rest_framework import status

from .serializers import DeviceManagerSerializer
from .models import DeviceManager

class DeviceManagerView(APIView):
    def get(self, request, pkID=-1):
        if pkID == -1 :
            data = DeviceManager.objects.all()
            response = DeviceManagerSerializer(data, many=True)
            return Response(response.data,status=status.HTTP_200_OK)
        else:
            data = DeviceManager.objects.get(pk=pkID)
            response = DeviceManagerSerializer(data)
            return Response(response.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        data = request.data
        response = DeviceManagerSerializer(data=data)
        if response.is_valid():
            response.save()
            return Response(response.data, status=status.HTTP_201_CREATED)
        else:
            return Response(response.errors, status=status.HTTP_400_BAD_REQUEST)

