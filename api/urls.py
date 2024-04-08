from django.urls import path
from data_processing.views import *

urlpatterns = [
    path('device_manager/', DeviceManagerView.as_view()),
    path('device_manager/<int:pkID>', DeviceManagerView.as_view()),
    path("forecast", Forecast.as_view()),
    path("view_emergency", EmergencyDataAPI.as_view()), 
    path("emergency", EmergencyVehicle.as_view()),
]
