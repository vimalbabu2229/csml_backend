from rest_framework.views import APIView
from rest_framework.response import Response    
from rest_framework import status
from rest_framework.parsers import FileUploadParser
import os

import numpy as np 
from io import BytesIO
import librosa
import pickle

from django.conf import settings

from .serializers import DeviceManagerSerializer, FileUploadSerializer
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


class Forecast(APIView):
    file_parser_classes = [FileUploadParser]

    def extract_features(self, y, sr):
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        rmse = librosa.feature.rms(y=y)[0]

        features = np.hstack((np.mean(mfccs, axis=1), 
                              np.mean(spectral_centroid), 
                              np.mean(spectral_rolloff), 
                              np.mean(zcr), 
                              np.mean(rmse)))
        return features
    
    def load_model(self):
        with open('resources/model.pkl', 'rb') as file:
            model = pickle.load(file)

        with open("resources/label_encoder.pkl", 'rb') as file :
            label_encoder = pickle.load(file)

        return (model, label_encoder)

    def post(self, request):
        file_upload_serializer = FileUploadSerializer(data=request.data)
        if file_upload_serializer.is_valid():
            audio = request.FILES['audio']
            file_buffer = BytesIO(audio.read())
            samples, sr = librosa.load(file_buffer)

            # loading model 
            model, label_encoder = self.load_model()
            input_feature_data = []
            for i in range(0, len(samples), (sr*5)):
                input_feature_data.append(self.extract_features(samples[i:(i+(sr*5))], sr))

            preds = model.predict(input_feature_data)
            aggregate_class_index = round(np.mean(preds))
            forecast = label_encoder.inverse_transform([aggregate_class_index])[0]
            # file_path = os.path.join(settings.MEDIA_ROOT, audio.name)
            # with open(file_path, 'wb+') as file:
                # for chunk in audio.chunks():
                    # file.write(chunk)

            return Response({'forecast': forecast}, status=status.HTTP_201_CREATED)
        else:
            return Response(file_upload_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
