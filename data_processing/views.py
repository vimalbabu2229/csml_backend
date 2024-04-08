from rest_framework.views import APIView
from rest_framework.response import Response    
from rest_framework import status
from rest_framework.parsers import FileUploadParser
import os
from .serializers import ForecastSerializer

import numpy as np 
from io import BytesIO
import librosa
import pickle
from datetime import datetime

from django.conf import settings

from .serializers import DeviceManagerSerializer
from .models import DeviceManager, ForecastModel

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
    
    # FEATURE EXTRATION
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
    
    # CALCULATE NOISE LEVEL
    def calculate_dB(self, samples):
        # Compute STFT
        D = librosa.stft(samples)

        # Calculate magnitude
        magnitude = np.abs(D)

        # Convert magnitude to Sound Pressure Level (SPL)
        reference_pressure = 20e-6  # Reference sound pressure level in pascals (20 µPa)
        magnitude_spl = 20 * np.log10(magnitude / reference_pressure)

        # Calculate average SPL
        average_spl = np.mean(magnitude_spl)
        return round(average_spl)

    # LOAD MODELS 
    def load_model(self):
        with open('resources/model.pkl', 'rb') as file:
            model = pickle.load(file)

        with open("resources/label_encoder.pkl", 'rb') as file :
            label_encoder = pickle.load(file)

        return (model, label_encoder)
    
    #GET 
    def get(self, request):
        data = ForecastModel.objects.all()
        response = ForecastSerializer(data, many=True)
        return Response(response.data, status=status.HTTP_200_OK)
    # POST 
    def post(self, request):
            device_id = request.headers.get('device')
            audio_data = request.body
            file_buffer = BytesIO(audio_data)
            samples, sr = librosa.load(file_buffer)

            # Loading model
            model, label_encoder = self.load_model()

            input_feature_data = []
            for i in range(0, len(samples), (sr * 5)):
                input_feature_data.append(self.extract_features(samples[i:(i + (sr * 5))], sr))

            preds = model.predict(input_feature_data)
            forecast = round(np.mean(preds))
            # forecast = label_encoder.inverse_transform([aggregate_class_index])[0]
            timestamp =  int(datetime.now().timestamp() * 1000)
            noise_level = self.calculate_dB(samples)

            data_to_db = {
                'forecast': forecast, 
                'timestamp': timestamp, 
                'noise_level' : noise_level,
                'device' : device_id
                }
            serializer = ForecastSerializer(data=data_to_db)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

