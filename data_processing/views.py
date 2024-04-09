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
from keras.models import load_model
import joblib
import time

from django.conf import settings

from .serializers import DeviceManagerSerializer
from .models import DeviceManager, ForecastModel, EmergencyData

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
        device_id = request.query_params.get('device', None)
        ago = request.query_params.get('ago', None)

        if device_id is not None and ago is not None:
            #Convert time_in_hours to seconds (1 hour = 3600 seconds)
            time_in_seconds = int(ago) * 3600 * 1000

            # Get the current time
            current_time = int(time.time())

            # Calculate the lower bound timestamp
            lower_bound_timestamp = current_time - time_in_seconds

            # Filter data based on device_id and timestamp
            data = ForecastModel.objects.filter(device_id=device_id, timestamp__gte=lower_bound_timestamp)
        else:
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


class EmergencyVehicle(APIView):
    file_parser_classes = [FileUploadParser]
    model = load_model('resources/model_em.h5')
    scaler = joblib.load('resources/scaler.joblib')

    def mfcc(self, y,sr=4000):
        return librosa.feature.mfcc(y=y,sr=sr, n_mfcc=12)


    def extract_mfccs(self, y):
        mfccs_list = []
        ran = len(y)//480
        for i in range(ran-10):
            y_clip = y[480*i:480*(i+1)]
            mfccs_clip = self.mfcc(y_clip)
            mfccs_clip = np.array(mfccs_clip)
            mfccs_clip = mfccs_clip.flatten()
            mfccs_list.append(mfccs_clip)
        return mfccs_list

    def predict_op(self, y, scaler):
        mfccs_list = self.extract_mfccs(y)
        scaler.transform(mfccs_list)
        count = 0
        N = 6
        th = 0.5
        
        prob_list = []
        class_list = []
        for i in range(N):
            p = self.model.predict(mfccs_list[i].reshape(1,12), batch_size=None, verbose=0)
            p = p.flatten()
            prob_list.append(p)
        prob = np.mean(prob_list)
        #print(prob)
        if prob > th:
            #print("Em")
            class_list.append(1)
        else:
            #print("Non-em")
            class_list.append(0)
        
        for i in range(N,len(mfccs_list)):
            prob_list.pop(0)
            p = self.model.predict(mfccs_list[i].reshape(1,12), batch_size=None, verbose=0)
            p = p.flatten()
            prob_list.append(p)
            prob = np.mean(prob_list)
            #print(prob)
            if prob > th:
                #print("Em")
                class_list.append(1)
            else:
                #print("Non-em")
                class_list.append(0)
        if np.mean(class_list) > 0.5:
            return 1
        else:
            return 0

    def post(self, request):
        print("****************")
        print("Ambulance Request = ", type(request.body))
        print("****************")
        
        audio_data = request.body
        file_buffer = BytesIO(audio_data)
        samples, sr = librosa.load(file_buffer ,sr=4000)

        emergency = self.predict_op(samples, self.scaler)

        if emergency == 1:
            EmergencyData.objects.create(
                device_id=request.headers['device'],  
            )

        return Response({'emergency': emergency}, status=status.HTTP_201_CREATED)


class EmergencyDataAPI(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve all emergency data
        data = list(EmergencyData.objects.values())
        print(data)
        
        # Clear the table after sending the data
        EmergencyData.objects.all().delete()
        
        # Send response
        return Response(data)